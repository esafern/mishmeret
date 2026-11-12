# Lessons learned - binding, not optional reading

Rules for any project run with Mishmeret: how a session checks, tests and reports. Each was learned on a real
project and is written here without that project's particulars. **Cite a lesson by NAME**: the name is its id,
never reused. A project adds its own lessons in its own file and points here for these. Under each rule, one
example from no project in particular: what the rule is there to avoid, and what it asks for.

- **DON'T FORGET MY LESSONS** - when a lesson already written down bites, the response is not
  optional: (1) acknowledge it WITH THE CODE - name the lesson, paste the lines, state what it said
  that you did anyway; (2) write, ten times, in the reply, `I will not <the specific thing>`.
  - *Avoid:* a deploy script is run without its dry run, again, after a lesson said to dry-run
    first, and the reply says "sorry, I will be more careful".
  - *Do:* the reply names the lesson, pastes the command that was run, says what the lesson said,
    and writes ten times "I will not run the deploy script without its dry run".
- **THE UNRUN CHECK** - a check not run on everything it applies to has verified nothing. If full
  coverage costs too much, say so and get a scope decision.
  - *Avoid:* a link checker is run on 50 of a site's 4,000 pages and the report says "no broken
    links".
  - *Do:* run it on all 4,000, or report "50 of 4,000 checked" and ask whether that is enough.
- **A SCORE IS NOT A CHECK** - a threshold is triage, not a certificate; look at what a passing
  result contains.
  - *Avoid:* an address matcher scores 0.93 against a 0.9 threshold, so the match is accepted - "12
    Oak St" with "12 Oak Ave".
  - *Do:* open a sample of what passed and read it; the threshold only decides what to look at
    first.
- **NO DERIVED GROUND TRUTH** - re-derive from primary sources (the original record, the raw input);
  trust no aggregate, including the project's own.
  - *Avoid:* a dashboard's monthly total is taken as the truth for a refund audit, and the job that
    built it skipped canceled orders.
  - *Do:* add up the orders table itself, and say where its total and the dashboard's differ.
- **FUZZY IS NOT A POSITION** - fuzzy matching cannot answer exact-position questions; anchor on an
  exact match first.
  - *Avoid:* a fuzzy search finds a clause in a 40-page contract with a score of 0.9, and the report
    says it is in paragraph 12 - that is a similar sentence; the clause is in paragraph 31.
  - *Do:* find the exact words first; where there is no exact match, say the place is not known.
- **EVERY ANCHOR HAS A GAP** - know a matching strategy's failure mode before reading its silence as
  correctness.
  - *Avoid:* customers are matched to accounts by email, no mismatch comes back, and the report says
    every customer has an account - the 300 customers with no email were never compared.
  - *Do:* list what the match cannot see (no email, two emails) and count those before saying
    "none".
- **ONE CAUSE IS NOT EVERY SYMPTOM** - after a fix, re-verify the original finding on corrected
  data.
  - *Avoid:* invoices total wrongly; a rounding bug is found and fixed; the ticket is closed.
  - *Do:* run the reported invoice again - it is still off, from a second cause (a tax applied
    twice).
- **CHEAP CHECKS CATCH OTHER THINGS** - run every independent check you have; mechanical ones catch
  what LLM ones miss.
  - *Avoid:* a model reviews a 300-row price list and finds nothing; nobody runs the one-line check
    for negative prices.
  - *Do:* run the checks for duplicates, ranges and totals as well; they take seconds and find a
    different kind of error.
- **TWO SIGNALS OR NONE** - require two independent signals to agree before trusting a fix.
  - *Avoid:* a spell checker suggests "Jon" should be "John", and the customer's name is changed.
  - *Do:* change it only when a second, independent source agrees (the signed order form); otherwise
    leave it and flag it.
- **THE PROMPT'S OWN BIAS** - fix the instruction, don't tune a threshold around its side effect.
  - *Avoid:* a prompt asks "find the errors in this paragraph"; the model reports errors in clean
    paragraphs; a confidence cutoff is raised to hide them.
  - *Do:* change the prompt to "say whether there is an error, and which" - the question was pushing
    the answer.
- **LOCALLY CLEAN, STILL BROKEN** - one instance resolving cleanly does not close what a structural
  check flagged.
  - *Avoid:* a check finds 41 footnote marks and 40 footnotes in a chapter; the first mark looked at
    has its note, so the flag is closed.
  - *Do:* keep it open until the count itself is explained - one mark still has no note.
- **THE KEY MUST HOLD THE QUESTION** - a cache key covers everything that changes the answer (a
  model's verdict on an input: the input's hash AND every option it was asked to choose between).
  - *Avoid:* a translation cache keyed on the sentence alone returns the French answer when German
    is asked for.
  - *Do:* the key holds the sentence, the target language and the model's version.
- **THE SECOND COPY OF THE TRUTH** - anything computable from another file is built by a script,
  never hand-maintained in parallel.
  - *Avoid:* a README's table of commands is typed by hand beside the code that defines them; a
    command is renamed and the table is wrong for a month.
  - *Do:* a script builds the table from the code, and a test fails when the two differ.
- **THE GREP THAT BEATS THE REVIEW** - run cheap pattern sweeps over the whole of the data after
  every batch of edits.
  - *Avoid:* forty configuration files are edited by hand and each is read over once.
  - *Do:* after the batch, one search across all of them for the old host name, an empty value, a
    doubled key.
- **WRITTEN IS NOT APPLIED** - verify every "fixed" claim against a diff of the data.
  - *Avoid:* "fixed the three wrong phone numbers" is reported because the update statement was
    written.
  - *Do:* compare the table before and after: three rows changed, to these three values.
- **EVERY PART, NOT PART ONE** - a loader that defaults to the first file is a silent scope bug.
  - *Avoid:* a report on "all orders" reads the first of three yearly files, because the loader
    takes the first when none is named.
  - *Do:* the loader reads every file, or refuses without a name; the report says which files it
    read.
- **FLAT COORDINATE KEYS** - pin a record's shape at the seam; prefer a loader that raises over one
  that returns nothing.
  - *Avoid:* one tool writes a point as x and y at the top of the record, another reads them from
    inside "pos" and falls back to nothing, so every point is silently missing.
  - *Do:* one loader that both use, which stops with an error on a record without x and y.
- **A SIGNAL THAT CANNOT DISAGREE** - before trusting a check, construct the input that MUST make it
  fail.
  - *Avoid:* a test named "passwords are hashed" passes; it would also pass with the hashing
    removed, because it compares the stored value with itself.
  - *Do:* before trusting it, give it a plain-text password and watch it fail.
- **THE FILTER THAT HIDES** - validate a filter by what it suppresses; silence is not correctness.
  - *Avoid:* a log filter drops "known noisy" warnings and the dashboard goes quiet; among the
    dropped lines is a new disk error with the same prefix.
  - *Do:* list what the filter removed and read it, before calling the quiet good.
- **THE SAMPLE THAT SELECTED ITSELF** - ask why these items got labeled before turning them into a
  rate.
  - *Avoid:* "95% of support tickets are about login" - counted from the tickets agents chose to
    tag, and they tag the easy ones.
  - *Do:* ask how the tagged tickets were picked; draw a random sample before quoting a rate.
- **WHERE YOU LOOKED, NOT WHERE IT IS** - sweep the whole of the data before calling it fixed.
  - *Avoid:* a date read month-first is fixed on the report page where it was noticed.
  - *Do:* search every place that parser is used: the export and the email template had it too.
- **THE FIELD NOBODY RENDERS** - for every new field: who displays it, and what does its reader do
  differently because of it?
  - *Avoid:* a "risk_score" is computed and stored on every order; no screen shows it and nobody
    acts on it.
  - *Do:* before adding it, name the screen that shows it and what the clerk does differently at a
    high score.
- **RETUNED TWICE, HAND IT BACK** - when your own fix regresses on measurement, revert and stop.
  - *Avoid:* a threshold change makes the results worse, a second makes them worse another way, and
    a third is tried.
  - *Do:* once your own fix regresses on the measure, revert it and hand the problem back with both
    measurements.
- **PRINTING IS NOT RUNNING** - a cheap detector belongs in the chain and writes an artifact.
  - *Avoid:* a script that finds duplicate customer records is run by hand once and its output read
    in the terminal.
  - *Do:* it runs in the nightly chain and writes a file; a later step fails if the file lists any.
- **STATE, NOT PRINTOUT** - check a tool's state and exit code, not its summary; a rebuild is done
  when the screen of the person it is for shows it.
  - *Avoid:* the backup tool prints "Backup complete" and that is reported; it exited with an error
    and the file is empty.
  - *Do:* read the exit code and the file's size; and the site is "rebuilt" when its owner's browser
    shows the new page.
- **SWEEP THE SIBLINGS** - when one branch of a function is wrong, read the others before writing
  the test.
  - *Avoid:* a discount function's "student" branch rounds wrongly; it is fixed and a test written
    for it.
  - *Do:* read the "senior" and "staff" branches first - they copy the same line.
- **APPLYING HAS SIDE EFFECTS** - a write to the source of truth updates, in the same step,
  everything else that describes it.
  - *Avoid:* a price is changed in the products table, and the search index, the cached page and the
    export still show the old one.
  - *Do:* the step that writes the price rebuilds or clears each of them, and a check compares them
    afterwards.
- **THE TEST PINNED TO THE DEFECT** - a test pinned to live data fails when the data improves; use
  fixture data and placeholder text.
  - *Avoid:* a test asserts that the live customer table has exactly three rows with no postcode;
    someone fills them in and the test fails.
  - *Do:* the test builds its own three placeholder rows and asserts that the code flags them.
- **DEFINED IS NOT COLLECTED** - cite test counts from `pytest --collect-only -q`, never from
  `grep`.
  - *Avoid:* "412 tests" is quoted from counting the lines that define one; thirty are never run (a
    repeated name, a misnamed file).
  - *Do:* quote the number the test runner itself collects.
- **THE VALUE CACHED AT LOAD** - when one payload feeds two views, the refresh path feeds both.
  - *Avoid:* one response fills both a table and a count badge; after an edit the table is refreshed
    and the badge keeps the old count.
  - *Do:* the refresh feeds both from the same new response.
- **THE SCAFFOLD NOBODY TOOK DOWN** - write down where a scaffold comes down; test the true-to-false
  leg of every sync.
  - *Avoid:* a redirect put in "until the migration is done" is still there a year later, and a
    switch is tested turning on but never off.
  - *Do:* write beside the redirect what removes it, and test the switch going back to off.
- **THE GUARD THAT TESTS A PROXY** - express a condition as the thing itself, not a symptom.
  - *Avoid:* "the user is an administrator" is tested as "the email ends with the company's domain".
  - *Do:* test the role itself.
- **THE MUTATION THAT DID NOT FAIL** - a surviving mutation is an unanswered question: is the test
  unable to see it or the code inert? Settle it before writing a comment that claims an effect.
  - *Avoid:* deleting a validation line changes no test's result, and a comment is added saying
    "validates the input".
  - *Do:* first find out whether the tests cannot see the line or the line does nothing; then fix
    the test or delete the line.
- **THE PROBE THAT CANNOT SEE** - in browser tests, scroll into view, assert on settled properties,
  fail loudly off-frame.
  - *Avoid:* a test clicks a button below the fold while the page is still moving; the click lands
    on nothing, and the test passes because it asserts nothing after it.
  - *Do:* scroll the button into view, wait until the page is still, assert what the click changed,
    and fail if the button is outside the window.
- **DO NOT MUTATE A TREE YOU ARE EDITING** - long verification runs on a snapshot; kill process
  trees and check for survivors.
  - *Avoid:* a twenty-minute test run is started in the folder you go on editing: it fails on a
    half-saved file, and stopping it leaves a worker still writing.
  - *Do:* run it on a snapshot; after stopping it, check that no child process survives.
- **PIXELS, NOT THE DOM** - when a reported UI symptom cannot be found in text, ask for a
  screenshot.
  - *Avoid:* a user says "the button is cut off"; the page's markup holds the whole label, so the
    report is closed.
  - *Do:* ask for a screenshot: the label is there and its box is clipped.
- **WIRED TO NOTHING** - hunt for features referenced only by tests, env vars read nowhere, flags
  never read, fields never consumed.
  - *Avoid:* a --verbose flag is parsed and never read; a documented environment variable has no
    reader; a function is called only by its own test.
  - *Do:* search for each one's reader, then connect it or delete it.
- **RENAME BY TOKEN, NOT REGEX** - derived files can be renamed, an append-only log cannot; walk
  NAME tokens.
  - *Avoid:* "id" is replaced with "uid" across a project by pattern: it hits "width" and "idle",
    and rewrites last year's audit log.
  - *Do:* rename the name tokens only, in files that are rebuilt; the append-only log keeps its old
    field.
- **SAY WHICH ONE YOU CHECKED** - name the file, the order and the rows; when the question is about
  the deliverable, check the deliverable.
  - *Avoid:* "I checked the export and it is sorted" - it was the staging copy, by date, the first
    twenty rows.
  - *Do:* say "production's export, by customer number, all 9,112 rows"; when the question is about
    what ships, check what ships.
- **REPRODUCE BEFORE YOU COMPARE** - prove the old code reproduces the committed file byte for byte
  before crediting a change with a diff. Rehearse on a copy (on macOS an APFS clone, `cp -c -R`).
  - *Avoid:* new code produces a different report and the difference is credited to the change; the
    old code no longer reproduces the stored report either, since a library moved.
  - *Do:* first make the old code give the stored file byte for byte, on a copy; then compare.
- **COUNT, DON'T CHOOSE BY EXAMPLE** - when two examples point opposite ways, count the class and
  write down what the rule costs.
  - *Avoid:* one example says strip trailing spaces, another says keep them, and the rule follows
    whichever was seen last.
  - *Do:* count: 1,940 rows gain from stripping and 12 lose; write the 12 down as what the rule
    costs.
- **THE CALLER DECIDES WHAT FAILURE MEANS** - a shared function reports failure; each caller decides
  what it implies.
  - *Avoid:* a shared fetch function returns an empty list on a network error, so the caller that
    deletes "items no longer on the server" deletes everything.
  - *Do:* the function reports the failure; the sync stops, and the display says "could not load".
- **EVERY PLATFORM IT WILL RUN ON** - for every change ask whether Windows, macOS or Linux could
  differ; if so, record the untested platforms where the change is recorded.
  - *Avoid:* a path is joined with "/" and a file opened with no encoding named, tested on one
    operating system.
  - *Do:* ask of each change whether another system differs; if it could and was not run there,
    write that beside the change.
- **WRITE THE ENUMERATION DOWN** - when a rule says "everything else that describes it", that
  everything is a list in code with one test over all of it.
  - *Avoid:* "when a product is renamed, update everything that mentions it" is done from memory,
    and the search index is forgotten.
  - *Do:* a list in code of every place that holds the name, one test that renames a product and
    checks each, and a second that searches the code and the schema for the name's field - every
    reader and writer of it - and fails on one the list lacks.
- **A PATH TURNED ON IS RUN FOR THE FIRST TIME** - run every input type through it on a clone.
  - *Avoid:* an "import from spreadsheet" feature written months ago and never enabled is switched
    on for everyone.
  - *Do:* on a copy, put every kind of file through it first: empty, huge, wrong columns, another
    encoding.
- **GUARD DATA BY PATH, NOT BY WRITER** - a list of redirected functions misses the next writer.
  - *Avoid:* three functions that write the accounts file are wrapped so tests cannot touch the real
    one; a fourth writer is added later, unwrapped.
  - *Do:* guard the file's path itself: any write to it from a test fails, whoever writes.
- **A SENTENCE OF ABSENCE IS A CLAIM** - "no record", "nothing", a zero, a missing mark: answered
  from the whole record, never from a view built for work still owed; a false one is reported at
  once, with the place it shows, whichever step will fix it.
  - *Avoid:* a customer's page says "No orders yet" because it reads the list of unshipped orders,
    and theirs have all shipped.
  - *Do:* answer "none" from the whole order history; and report the false line the day it is found,
    with its address.
- **A WRONG VALUE IS WORSE THAN A "?"** - where its signals disagree and none can be confirmed, a
  number, place or reading is shown unknown, never guessed.
  - *Avoid:* two sources give a delivery date of the 3rd and the 13th, and the page shows the 3rd.
  - *Do:* show "date unknown" until one of them is confirmed.
- **DON'T REINVENT THE WHEEL** - before writing code, look for code that already solves the problem
  or can perform the action, and use it; two paths for one job drift apart. Whoever reviews a plan
  or a build looks for it.
  - *Avoid:* a new date-formatting helper is written beside the one the project already has, and the
    two come to differ on time zones.
  - *Do:* search first and use the one that exists; whoever reviews the plan asks "what already does
    this?".
- **ASK WHY BEFORE DESIGNING FOR A GAP** - a measured gap in coverage (inputs not read, cases not
  reached) is traced against the whole record before code, a plan or a sentence treats it as given.
  - *Avoid:* 8% of uploaded receipts are "not processed", and a retry queue is designed for them.
  - *Do:* trace the 8% first: all come from one phone model's image format - a one-line fix, and no
    queue.
