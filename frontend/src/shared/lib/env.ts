import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url(),
  NEXT_PUBLIC_WS_BASE_URL: z
    .string()
    .refine(
      (val) => val.startsWith("ws://") || val.startsWith("wss://") || z.string().url().safeParse(val).success,
      { message: "Must be a valid WebSocket URL (ws:// or wss://)" }
    ),
  NEXT_PUBLIC_APP_ENV: z.enum(["development", "staging", "production"]),
});

export type Env = z.infer<typeof envSchema>;

function getEnv(): Env {
  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_WS_BASE_URL: process.env.NEXT_PUBLIC_WS_BASE_URL,
    NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV || "development",
  });

  if (!parsed.success) {
    console.error("Invalid environment variables:", parsed.error.flatten().fieldErrors);
    throw new Error("Invalid environment variables");
  }

  return parsed.data;
}

export const env = getEnv();
