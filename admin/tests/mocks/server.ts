import { setupServer } from "msw/node";
import { authHandlers } from "./handlers/auth";
import { metricsHandlers } from "./handlers/metrics";
import { usersHandlers } from "./handlers/users";

/** @module tests/mocks/server — setupServer (Node) para Vitest. */
export const server = setupServer(
	...authHandlers,
	...usersHandlers,
	...metricsHandlers,
);
