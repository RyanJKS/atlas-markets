# User applications

Put deployable user applications here, such as a trader workstation or an operations
console. No frontend is implemented yet. Each application owns its package manifest,
tests, build output, and Dockerfile when containerized. Use a frontend workspace when
the first application is added. The Python workspace does not manage JavaScript dependencies.

Applications call service APIs. They must not import service source code or access
service databases directly.
