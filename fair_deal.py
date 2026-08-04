# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class FairDeal(gl.Contract):
    buyer: Address
    seller: Address
    amount_locked: u256
    is_released: bool
    description: str
    is_disputed: bool
    dispute_reason: str
    seller_evidence: str
    is_resolved: bool
    winner: str
    resolution_reason: str

    def __init__(self, seller: str, description: str):
        self.buyer = gl.message.sender_address
        self.seller = Address(seller)
        self.amount_locked = u256(0)
        self.is_released = False
        self.description = description
        self.is_disputed = False
        self.dispute_reason = ""
        self.seller_evidence = ""
        self.is_resolved = False
        self.winner = ""
        self.resolution_reason = ""

    @gl.public.write.payable
    def fund_deal(self) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can fund this deal."
        assert not self.is_released, "This deal is already completed."
        self.amount_locked += gl.message.value

    @gl.public.write
    def release_funds(self) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can release funds."
        assert not self.is_released, "Funds already released."
        assert self.amount_locked > 0, "No funds to release."

        self.is_released = True
        recipient = gl.get_contract_at(self.seller)
        recipient.emit_transfer(value=self.amount_locked)

    @gl.public.write
    def open_dispute(self, reason: str) -> None:
        assert gl.message.sender_address == self.buyer, "Only the buyer can open a dispute."
        assert not self.is_released, "This deal is already completed."
        assert self.amount_locked > 0, "No funds have been locked yet."
        assert not self.is_disputed, "A dispute is already open."

        self.is_disputed = True
        self.dispute_reason = reason

    @gl.public.write
    def submit_seller_evidence(self, evidence: str) -> None:
        assert gl.message.sender_address == self.seller, "Only the seller can submit evidence."
        assert self.is_disputed, "There is no open dispute."
        assert not self.is_resolved, "This dispute is already resolved."

        self.seller_evidence = evidence

    @gl.public.write
    def resolve_dispute(self) -> None:
        assert self.is_disputed, "There is no open dispute to resolve."
        assert not self.is_resolved, "This dispute is already resolved."

        verdict_prompt = f"""
        You are a fair, impartial judge resolving a payment dispute between a buyer and seller.

        Deal description: "{self.description}"
        Buyer's complaint: "{self.dispute_reason}"
        Seller's evidence/response: "{self.seller_evidence}"

        Decide who should receive the locked funds. Reply with ONLY one single word:
        "seller" if the seller delivered what was promised and should be paid,
        "buyer" if the seller did not deliver and the buyer should be refunded.
        No punctuation, no extra words, nothing else.
        """

        def get_verdict():
            res = gl.nondet.exec_prompt(verdict_prompt)
            return res.strip().lower()

        winner = gl.eq_principle.strict_eq(get_verdict)

        reason_prompt = f"""
        You are a fair, impartial judge. You just decided that the "{winner}" should receive
        the funds in this dispute:
        Deal description: "{self.description}"
        Buyer's complaint: "{self.dispute_reason}"
        Seller's evidence: "{self.seller_evidence}"

        Write one short, clear sentence (max 25 words) explaining why.
        Reply with ONLY the sentence, nothing else.
        """

        def get_reason():
            return gl.nondet.exec_prompt(reason_prompt).strip()

        reason = gl.eq_principle.prompt_comparative(
            get_reason,
            principle="Both responses give a short, clear explanation for the same judgment, even if worded differently."
        )

        self.winner = winner
        self.resolution_reason = reason
        self.is_resolved = True
        self.is_released = True

        if winner == "seller":
            recipient = gl.get_contract_at(self.seller)
        else:
            recipient = gl.get_contract_at(self.buyer)

        recipient.emit_transfer(value=self.amount_locked)

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
        return f"Reason: {self.dispute_reason} | Seller evidence: {self.seller_evidence} | Winner: {self.winner} | Explanation: {self.resolution_reason}"
