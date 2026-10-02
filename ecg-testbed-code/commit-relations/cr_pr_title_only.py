"""Key appears only in the PR title, not in any commit.

Fulfilled: ECT-10022 names this file in the PR title that merged this
change, and nowhere else - not in this commit message, not in the file
body. A Code->Jira reader that only scans commit messages and code text
must miss this edge; one that also reads merged PR titles must find it.
"""
