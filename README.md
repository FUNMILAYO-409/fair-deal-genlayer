Fair Deal, An AI-Powered Escrow & Dispute Resolution

Fair Deal is an escrow contract built on GenLayer that removes the need for a human middleman in online trades. It holds a buyer's payment, releases it once the buyer is satisfied, and if something goes wrong, lets an AI judge review both sides of a dispute and decide who gets paid, using GenLayer's Optimistic Democracy consensus.

Live app: https://funmilayo-409.github.io/fair-deal-genlayer/
Deployed contract (GenLayer Studio network): 0x3bfC8E3b5bE9869460d0BA0C97c2A4B4cC21410d

The problem

Every day, people trade online with no real protection: a freelancer paid upfront who never delivers, a buyer who claims work was never done, a Discord trade gone sideways. Right now, resolving these disputes means trusting a platform, a moderator, or just hoping the other side is honest. There's no fast, fair, automated way to settle a disagreement  until now.

 How Fair Deal works

1. Fund the deal : the buyer locks payment into the contract. It's held safely, nobody can touch it unilaterally.
2. Release funds : if the buyer is happy with what they received, they approve, and the seller is paid automatically.
3. Open a dispute : if the buyer isn't satisfied, they open a dispute and explain what went wrong.
4. Submit evidence : the seller responds with their side and any proof of delivery.
5. AI resolution : either party can trigger (resolve_dispute) GenLayer's validators , each running an independent LLM read the deal description, the buyer's complaint, and the seller's evidence, and reach consensus on who should be paid. The verdict and reasoning are recorded permanently on-chain, and funds are released automatically to the winner.

This isn't a single AI making a call in isolation, it's GenLayer's Optimistic Democracy consensus. Multiple validators independently reason through the same evidence and must reach equivalent conclusions (not identical wording, but the same underlying verdict) before the network accepts the result.

Why this matters :

Traditional smart contracts can move money, but they can't judge anything subjective , they only understand exact, predefined conditions. Fair Deal shows what becomes possible when a contract can actually reason about evidence, real dispute resolution without a platform fee, a support ticket queue, or a biased human arbitrator.

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
 `submit_seller_evidence(evidence)` / Seller | Responds to a dispute with proof/explanation /
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

In testing, a buyer disputed a deal for a Twitter article, claiming the work was never delivered. The seller responded with a link to the actual posted thread as proof. The AI judge reviewed both sides and ruled in the seller's favor, explaining: Seller provided verifiable proof of delivery via the posted Twitter thread, so the buyer's claim that no work was delivered is not supported. In an earlier test, the AI ruled the opposite way , a seller submitted an unrelated link as false proof, and the AI correctly caught the mismatch and ruled for the buyer. Together, these show the AI judge basing its decision on the actual evidence each time, not a fixed or biased outcome.
