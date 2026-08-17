# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import datetime

class FairDeal(gl.Contract):
    buyer: Address
    seller: Address
    amount_locked: u256
    is_released: bool
    description: str
    is_disputed: bool
    dispute_reason: str
    seller_evidence: str
    seller_evidence_url: str
    is_resolved: bool
    winner: str
    resolution_reason: str
    response_window_seconds: u256
    dispute_opened_at: u256

    def __init__(self, seller: str, description: str, response_window_seconds: int):
        self.buyer = gl.message.sender_address
        self.seller = Address(seller)
        self.amount_locked = u256(0)
        self.is_released = False
        self.description = description
        self.is_disputed = False
        self.dispute_reason = ""
        self.seller_evidence = ""
        self.seller_evidence_url = ""
        self.is_resolved = False
        self.winner = ""
        self.resolution_reason = ""
        self.response_window_seconds = u256(response_window_seconds)
        self.dispute_opened_at = u256(0)

    @gl.public.write.payable
    def fund_deal(self) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can fund this deal."
        assert not self.is_released, "This deal is already completed."
        self.amount_locked += gl.message.value

    @gl.public.write
    def release_funds(self) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can release funds."
        assert not self.is_released, "Funds already released."
        assert not self.is_disputed, "This deal is under dispute and cannot be released manually. Use resolve_dispute instead."
        assert self.amount_locked > 0, "No funds to release."

        payout = self.amount_locked
        self.is_released = True
        self.amount_locked = u256(0)
        recipient = gl.get_contract_at(self.seller)
        recipient.emit_transfer(value=payout)

    @gl.public.write
    def open_dispute(self, reason: str) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can open a dispute."
        assert not self.is_released, "This deal is already completed."
        assert self.amount_locked > 0, "No funds have been locked yet."
        assert not self.is_disputed, "A dispute is already open."

        self.is_disputed = True
        self.dispute_reason = reason
        self.dispute_opened_at = u256(int(datetime.datetime.now().timestamp()))

    @gl.public.write
    def submit_seller_evidence(self, evidence: str, evidence_url: str = "") -> None:
        assert gl.message.sender_address == self.seller, "Only the seller can submit evidence."
        assert self.is_disputed, "There is no open dispute."
        assert not self.is_resolved, "This dispute is already resolved."
        assert len(evidence.strip()) > 0, "Evidence cannot be empty."

        now = int(datetime.datetime.now().timestamp())
        elapsed = now - int(self.dispute_opened_at)
        assert elapsed < int(self.response_window_seconds), "The response deadline has already passed. The buyer may now claim a timeout refund; evidence can no longer be submitted for this dispute."

        self.seller_evidence = evidence
        self.seller_evidence_url = evidence_url.strip()

    @gl.public.write
    def resolve_dispute(self) -> None:
        sender = gl.message.sender_address
        assert sender == self.buyer or sender == self.seller, "Only the buyer or seller can trigger resolution."
        assert self.is_disputed, "There is no open dispute to resolve."
        assert not self.is_released, "This deal is already completed."
        assert not self.is_resolved, "This dispute is already resolved."
        assert len(self.seller_evidence.strip()) > 0, "Resolution requires the seller to submit evidence first. If the seller never responds, use claim_timeout_refund once the response window has passed."

        description = self.description
        dispute_reason = self.dispute_reason
        seller_evidence = self.seller_evidence
        evidence_url = self.seller_evidence_url

        def get_verdict():
            fetched_content = ""
            if evidence_url:
                try:
                    fetched_content = gl.nondet.web.render(evidence_url, mode='text')[:3000]
                except Exception:
                    fetched_content = "(Could not retrieve the submitted link.)"

            verdict_prompt = f"""
            You are a fair, impartial judge resolving a payment dispute between a buyer and seller.

            Deal description: "{description}"
            Buyer's complaint: "{dispute_reason}"
            Seller's written response: "{seller_evidence}"
            Actual content retrieved from the seller's submitted evidence link (if any): "{fetched_content}"

            Base your decision on the ACTUAL retrieved content where available, not just the
            seller's claim. Decide who should receive the locked funds. Reply with ONLY one
            single word: "seller" or "buyer". No punctuation, no extra words, nothing else.
            """

            for _ in range(3):
                res = gl.nondet.exec_prompt(verdict_prompt).strip().lower()
                if res in ("buyer", "seller"):
                    return res
            raise Exception("Judge failed to produce a valid buyer/seller verdict.")

        winner = gl.eq_principle.strict_eq(get_verdict)
        assert winner in ("buyer", "seller"), "Invalid verdict produced."

        reason_prompt = f"""
        You are a fair, impartial judge. You just decided that the "{winner}" should receive
        the funds in this dispute:
        Deal description: "{description}"
        Buyer's complaint: "{dispute_reason}"
        Seller's evidence: "{seller_evidence}"

        Write one short, clear sentence (max 25 words) explaining why.
        Reply with ONLY the sentence, nothing else.
        """

        def get_reason():
            return gl.nondet.exec_prompt(reason_prompt).strip()

        reason = gl.eq_principle.prompt_comparative(
            get_reason,
            principle="Both responses give a short, clear explanation for the same judgment, even if worded differently."
        )

        payout = self.amount_locked

        self.winner = winner
        self.resolution_reason = reason
        self.is_resolved = True
        self.is_released = True
        self.amount_locked = u256(0)

        if winner == "seller":
            recipient = gl.get_contract_at(self.seller)
        else:
            recipient = gl.get_contract_at(self.buyer)

        recipient.emit_transfer(value=payout)

    @gl.public.write
    def claim_timeout_refund(self) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can claim a timeout refund."
        assert self.is_disputed, "There is no open dispute."
        assert not self.is_released, "This deal is already completed."
        assert not self.is_resolved, "This dispute is already resolved."
        assert len(self.seller_evidence.strip()) == 0, "The seller has already submitted evidence; use resolve_dispute instead."

        now = int(datetime.datetime.now().timestamp())
        elapsed = now - int(self.dispute_opened_at)
        assert elapsed >= int(self.response_window_seconds), "The response deadline has not passed yet."

        payout = self.amount_locked

        self.winner = "buyer"
        self.resolution_reason = "The seller did not respond within the response deadline; funds were returned to the buyer by timeout."
        self.is_resolved = True
        self.is_released = True
        self.amount_locked = u256(0)

        recipient = gl.get_contract_at(self.buyer)
        recipient.emit_transfer(value=payout)

    @gl.public.view
    def get_status(self) -> str:
        if self.is_resolved:
            return f"Dispute resolved - funds sent to {self.winner}"
        elif self.is_disputed:
            return "Disputed - awaiting resolution"
        elif self.is_released:
            return "Completed - funds released to seller"
        elif self.amount_locked > 0:
            return "Funded - waiting for buyer approval"
        else:
            return "Waiting for buyer to fund the deal"

    @gl.public.view
    def get_details(self) -> str:
        return f"Buyer: {self.buyer} | Seller: {self.seller} | Locked: {self.amount_locked} | Description: {self.description}"

    @gl.public.view
    def get_dispute_info(self) -> str:
        return f"Reason: {self.dispute_reason} | Seller evidence: {self.seller_evidence} | Evidence URL: {self.seller_evidence_url} | Winner: {self.winner} | Explanation: {self.resolution_reason}"

    @gl.public.view
    def get_response_deadline_info(self) -> str:
        if not self.is_disputed:
            return "No dispute is currently open."
        now = int(datetime.datetime.now().timestamp())
        elapsed = now - int(self.dispute_opened_at)
        remaining = int(self.response_window_seconds) - elapsed
        if remaining < 0:
            remaining = 0
        return f"Response window: {int(self.response_window_seconds)}s | Elapsed: {elapsed}s | Remaining: {remaining}s"
