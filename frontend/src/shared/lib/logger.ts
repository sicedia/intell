/**
 * Simple logger utility for development.
 * Logs are disabled in production builds.
 */

const isDev = process.env.NODE_ENV === "development";

type LogLevel = "debug" | "info" | "warn" | "error";

interface LoggerOptions {
    context?: string;
}

function formatMessage(context: string | undefined, message: string): string {
    return context ? `[${context}] ${message}` : message;
}

/**
 * Development-only logger.
 * All logs are no-ops in production for performance.
 */
export const logger = {
    debug: (message: string, ...args: unknown[]) => {
        if (isDev) {
            console.debug(message, ...args);
        }
    },

    info: (message: string, ...args: unknown[]) => {
        if (isDev) {
            console.info(message, ...args);
        }
    },

    warn: (message: string, ...args: unknown[]) => {
        if (isDev) {
            console.warn(message, ...args);
        }
    },

    error: (message: string, ...args: unknown[]) => {
        if (isDev) {
            console.error(message, ...args);
        }
    },
};

/**
 * Create a scoped logger with a context prefix.
 * 
 * @example
 * const log = createLogger("DownloadZip");
 * log.error("Failed to download"); // Outputs: [DownloadZip] Failed to download
 */
export function createLogger(context: string) {
    return {
        debug: (message: string, ...args: unknown[]) => {
            logger.debug(formatMessage(context, message), ...args);
        },
        info: (message: string, ...args: unknown[]) => {
            logger.info(formatMessage(context, message), ...args);
        },
        warn: (message: string, ...args: unknown[]) => {
            logger.warn(formatMessage(context, message), ...args);
        },
        error: (message: string, ...args: unknown[]) => {
            logger.error(formatMessage(context, message), ...args);
        },
    };
}
