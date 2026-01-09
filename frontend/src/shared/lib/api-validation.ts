import { z } from "zod";

/**
 * Optional validation helper for API responses
 * Use this when you want to validate API responses with Zod schemas
 */
export function validateResponse<T>(
    data: unknown,
    schema: z.ZodSchema<T>
): T {
    const result = schema.safeParse(data);
    if (!result.success) {
        console.error("API response validation failed:", result.error);
        throw new Error(`Invalid API response: ${result.error.message}`);
    }
    return result.data;
}

/**
 * Safe validation that returns the data or a fallback
 */
export function validateResponseSafe<T>(
    data: unknown,
    schema: z.ZodSchema<T>,
    fallback: T
): T {
    const result = schema.safeParse(data);
    if (!result.success) {
        console.warn("API response validation failed, using fallback:", result.error);
        return fallback;
    }
    return result.data;
}
