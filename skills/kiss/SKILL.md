---
name: kiss
description: "Close a decision that has several valid options by picking the smallest option that meets the actual requirement, writing the decision into the decision doc or ticket, and parking every non-essential refinement as an explicit to-refine-later item. Use when: a decision has several valid options, a design or process discussion keeps growing, or an open decision needs to be closed. Triggers: KISS, keep it simple, simplest option, smallest option, lock the decision, park the rest."
license: MIT
---

# KISS decision

Close the decision with the smallest option that meets the actual requirement. Write the decision where the team reads
it, and park everything else as named follow-ups instead of deciding it now.

1. State the requirement in one sentence: what the decision must achieve now, taken from the ticket, the doc, or the
   user. Hard constraints such as safety, legal, and security belong to the requirement. "Might need later", edge cases
   nobody has hit, and nice-to-haves are refinements. If the requirement is unclear, ask one question before choosing.
2. List the valid options, including the existing behavior when it is valid. Give each one line: what it is and what it
   adds in parts, people, tools, steps, or rules.
3. Pick the smallest option that fully meets the requirement. Smallest means the fewest new parts, people, tools, steps,
   and rules; prefer what already exists. Drop options that do more than the requirement asks, even when they are better
   in theory. If no option meets the requirement, say so and stop.
4. Write the decision into the doc, ticket, or thread that owns it, not only into the chat. Use the doc's language and
   this shape:

   ```markdown
   **Decision (YYYY-MM-DD):** <chosen option in one sentence>.
   **Why:** <the requirement it meets, and why the larger options are not needed now>.
   **To refine later:**
   - <refinement> — revisit when <trigger>.
   ```

   Where the doc tracks status, such as a summary table, a tag, or a label, mark the decision as decided.
5. Park the rest. Put every option, variant, or idea that was raised and not chosen under "To refine later", each with
   a trigger such as "after the pilot" or "when a second team uses it". Do not decide these now. Move an idea that
   belongs to another topic to that topic and link it, instead of folding it into this decision.
6. Report the requirement, the chosen option, the parked items, and every place you edited. Ask before you edit a doc
   or ticket that others read or that publishes outside the conversation.

Keep the rationale to two or three sentences. The smallest option still has to meet the whole requirement; an option
that skips part of it is not smaller, it is incomplete.
