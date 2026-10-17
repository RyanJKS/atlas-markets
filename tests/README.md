# Cross-service tests

Service unit and HTTP tests live beside each service in `services/<name>/tests/`.
Add integration and end-to-end tests here when services communicate. Cover event
compatibility, duplicate delivery, ordering, failure recovery, and the complete
simulated trade flow. Add this directory to the root pytest `testpaths` when tests
are introduced. There are no cross-service workflows to test yet.
