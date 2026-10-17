# Execution simulator placeholder

Planned responsibility: consume accepted orders and produce reproducible simulated
fills, including partial fills and rejected executions. This service will not connect
to a real broker. Orders retains ownership of the order lifecycle.

Status: documentation only. There is no Python project, HTTP server, Dockerfile,
broker connection, or execution logic. This directory is excluded from the UV workspace
until implementation starts. See [service boundaries](../README.md).
