Fair Deal, An AI-Powered Escrow & Dispute Resolution

Fair Deal is an escrow contract built on GenLayer that removes the need for a human middleman in online trades. It holds a buyer's payment, releases it once the buyer is satisfied, and if something goes wrong, lets an AI judge review both sides of a dispute and decide who gets paid, using GenLayer's Optimistic Democracy consensus.

Live app: https://funmilayo-409.github.io/fair-deal-genlayer/
Deployed contract (GenLayer Studio network): 0xf22574880AA94aB60590aEce6A4716Dc4e2B5b5D

The problem

Every day, people trade online with no real protection: a freelancer paid upfront who never delivers, a buyer who claims work was never done, a Discord trade gone sideways. Right now, resolving these disputes means trusting a platform, a moderator, or just hoping the other side is honest. There's no fast, fair, automated way to settle a disagreement  until now.

 How Fair Deal works

1. Fund the deal : the buyer locks payment into the contract. It's held safely, nobody can touch it unilaterally.
2. Release funds : if the buyer is happy with what they received, they approve, and the seller is paid automatically.
3. Open a dispute : if the buyer isn't satisfied, they open a dispute and explain what went wrong.
4. Submit evidence : the seller responds with their side and any proof of delivery, there is also a tab for link to the evidence provided.
5. AI resolution : either party can trigger (resolve_dispute) GenLayer's validators , each running an independent LLM read the deal description, the buyer's complaint, and the seller's evidence, and reach consensus on who should be paid. The verdict and reasoning are recorded permanently on-chain, and funds are released automatically to the winner.

This isn't a single AI making a call in isolation, it's GenLayer's Optimistic Democracy consensus. Multiple validators independently reason through the same evidence and must reach equivalent conclusions (not identical wording, but the same underlying verdict) before the network accepts the result.

Why this matters :

Traditional smart contracts can move money, but they can't judge anything subjective , they only understand exact, predefined conditions. Fair Deal shows what becomes possible when a contract can actually reason about evidence, real dispute resolution without a platform fee, a support ticket queue, or a biased human arbitrator.

time-out protection: 

If a seller never responds to a dispute, funds could otherwise stay locked forever. To prevent this, opening a dispute starts a response deadline. If the seller hasn't submitted evidence once that window passes, the buyer can call claim_timeout_refund to reclaim their funds directly, no AI judgment needed, since there's nothing to evaluate if the seller never showed up. This path is blocked the moment the seller actually submits evidence, so it can't be used to bypass a real resolution. Covered by contract tests in test_fair_deal_timeout.py.

Tech stack :
Contract: Python, using GenLayer's (gl.Contract framework).
Consensus: GenLayer's Optimistic Democracy  (gl.eq_principle.strict_eq) for the binary verdict, (gl.eq_principle.prompt_comparative) for the AI's written explanation (since exact wording naturally varies between validators, but the underlying reasoning should agree)
Frontend: Single-page vanilla HTML/JS app using GenLayer's official (genlayer-js` SDK) connected via MetaMask
Hosting: GitHub Pages

Contract methods :

 `Method`/ Who can call it / What it does 
 `fund_deal` / Buyer / Locks payment into the contract /
` release_funds` / Buyer / Approves and pays the seller /
 `open_dispute(reason)` / Buyer / Flags a problem with the deal /
 `submit_seller_evidence(evidence)` / Seller | Responds to a dispute with proof/explanation / and url link to the evidence
 `resolve_dispute` / Either party / Triggers the AI judge to review both sides and release funds to the winner /
 `get_status` / Anyone (read-only) / Current state of the deal /
 `get_details` / Anyone (read-only) / Buyer, seller, amount locked, description /
 `get_dispute_info` / Anyone (read-only) / Dispute reason, evidence, verdict, and AI's explanation /

 Try it yourself

1. Open the [live app](https://funmilayo-409.github.io/fair-deal-genlayer/)
2. Connect a MetaMask wallet on the GenLayer Studio network
3. Deploy your own instance of (fair_deal.py) in [GenLayer Studio](https://studio.genlayer.com), or use the deployed contract address above
4. Paste the contract address into the app and click Load Deal

Real example

Fair Deal's dispute resolution actually fetches and reads submitted evidence links rather than trusting a seller's written claim alone. Two contrasting tests show it responding to what it actually finds:

Unverifiable evidence is ruled for the buyer. A seller submitted a link to an X (Twitter) post as proof of a delivered thread. X's pages are heavily JavaScript-rendered, so the retrieved content came back empty. The AI judge correctly ruled it couldn't verify the claim: "the seller provided no verifiable proof of delivering the thread, the buyer is entitled to a refund."
Verifiable evidence is ruled for the seller. A seller submitted a link to a plain-text page (this repo's own README) as proof of a completed deliverable. The AI judge retrieved the real content and ruled: "the seller provided a verifiable link to the completed README, satisfying the agreed deliverable, so payment is warranted."
