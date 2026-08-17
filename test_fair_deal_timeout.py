"""
Tests for Fair Deal's timeout custody path.

This covers the scenario the reviewer flagged: a seller can lock a buyer's
funds indefinitely by never responding to a dispute. These tests prove that
after the response window passes with no seller evidence, the buyer can
reclaim their funds directly via claim_timeout_refund() -- and that they
CANNOT do so before the deadline, and CANNOT do so once the seller has
actually responded. Also covers that the seller cannot submit evidence
after the deadline has passed, closing the race condition between
submit_seller_evidence and claim_timeout_refund.

Run with: gltest test_fair_deal_timeout.py
(requires: pip install genlayer-test)

Note: the contract file is referenced at the repository root
(fair_deal.py), matching the actual layout of this repo.
"""

import time
import pytest


def test_buyer_cannot_claim_timeout_before_deadline(direct_deploy, direct_vm, direct_alice, direct_bob):
    """The buyer should not be able to reclaim funds before the response window has passed."""
    with direct_vm.prank(direct_alice):
        contract = direct_deploy(
            "fair_deal.py",
            str(direct_bob),
            "Payment for a Twitter thread about GenLayer",
            5,  # response_window_seconds
        )
        contract.fund_deal(value=100)
        contract.open_dispute(args=["Seller never delivered anything"])

        with direct_vm.expect_revert("deadline has not passed"):
            contract.claim_timeout_refund()


def test_buyer_can_claim_timeout_after_deadline(direct_deploy, direct_vm, direct_alice, direct_bob):
    """
    Core custody-path test: if the seller never submits evidence, the buyer
    must be able to reclaim their funds once the response window elapses.
    """
    with direct_vm.prank(direct_alice):
        contract = direct_deploy(
            "fair_deal.py",
            str(direct_bob),
            "Payment for a Twitter thread about GenLayer",
            2,  # short response window for testing
        )
        contract.fund_deal(value=100)
        contract.open_dispute(args=["Seller never delivered anything"])

    # Simulate the response window elapsing with no seller action.
    time.sleep(3)

    with direct_vm.prank(direct_alice):
        contract.claim_timeout_refund()

    status = contract.get_status().call()
    assert "buyer" in status.lower()

    details = contract.get_details().call()
    assert "Locked: 0" in details


def test_seller_cannot_claim_timeout_refund(direct_deploy, direct_vm, direct_alice, direct_bob):
    """Only the buyer should be able to trigger a timeout refund."""
    with direct_vm.prank(direct_alice):
        contract = direct_deploy(
            "fair_deal.py",
            str(direct_bob),
            "Payment for a Twitter thread about GenLayer",
            2,
        )
        contract.fund_deal(value=100)
        contract.open_dispute(args=["Seller never delivered anything"])

    time.sleep(3)

    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("Only the buyer can claim"):
            contract.claim_timeout_refund()


def test_timeout_claim_blocked_once_seller_responds(direct_deploy, direct_vm, direct_alice, direct_bob):
    """
    Once the seller has actually submitted evidence, the buyer should no
    longer be able to bypass judgment via a timeout claim -- resolve_dispute
    is the correct path at that point, not claim_timeout_refund.
    """
    with direct_vm.prank(direct_alice):
        contract = direct_deploy(
            "fair_deal.py",
            str(direct_bob),
            "Payment for a Twitter thread about GenLayer",
            5,
        )
        contract.fund_deal(value=100)
        contract.open_dispute(args=["Seller never delivered anything"])

    with direct_vm.prank(direct_bob):
        contract.submit_seller_evidence(args=["I delivered it, here is proof", ""])

    time.sleep(6)

    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("already submitted evidence"):
            contract.claim_timeout_refund()


def test_seller_cannot_submit_evidence_after_deadline(direct_deploy, direct_vm, direct_alice, direct_bob):
    """
    Closes the race condition the reviewer flagged: once the response
    deadline has passed, the seller can no longer submit evidence at all,
    even if claim_timeout_refund hasn't been called yet. Only one path
    should ever be valid at a time.
    """
    with direct_vm.prank(direct_alice):
        contract = direct_deploy(
            "fair_deal.py",
            str(direct_bob),
            "Payment for a Twitter thread about GenLayer",
            2,  # short response window for testing
        )
        contract.fund_deal(value=100)
        contract.open_dispute(args=["Seller never delivered anything"])

    # Let the deadline pass without the buyer claiming a refund yet.
    time.sleep(3)

    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("deadline has already passed"):
            contract.submit_seller_evidence(args=["I delivered it, here is proof", ""])
