import { setupWorker } from "msw/browser";
import { authHandlers } from "./handlers/auth";
import { metricsHandlers } from "./handlers/metrics";
import { usersHandlers } from "./handlers/users";

/** @module tests/mocks/browser — setupWorker (browser dev con NEXT_PUBLIC_USE_MSW). */
export const worker = setupWorker(
	...authHandlers,
	...usersHandlers,
	...metricsHandlers,
);
