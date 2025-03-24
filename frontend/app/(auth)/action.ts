"use server";

import { z } from "zod";


// import { createUser, getUser } from '@/lib/db/queries';

import { signIn } from "./auth";

const authFormSchema = z.object({
  username: z.string().min(4),
  password: z.string().min(6),
});
export interface LoginActionState {
  status: "idle" | "in_progress" | "success" | "failed" | "invalid_data";
}

const BACKEND_API_URL = process.env.BACKEND_API_URL!;
export const login = async (
  _: LoginActionState,
  formData: FormData
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      username: formData.get("username"),
      password: formData.get("password"),
    });

    const body = new URLSearchParams();
    body.append("username", validatedData.username);
    body.append("password", validatedData.password);

    const response = await fetch(`${BACKEND_API_URL}/api/auth/login`, {
      method: "POST",
      body: body,
    });

    if (!response.ok) {
      return {
        status: "failed",
      };
    }
    const data = await response.json();

    await signIn("credentials", {
      username: validatedData.username,
      accessToken: data.access_token,
      user: JSON.stringify(data.user),
      redirect: false,
    });
    return { status: "success" };
  } catch (error) {
    console.log(error);
    return {
      status: "failed",
    };
  }
};

export interface RegisterActionState {
  status:
    | "idle"
    | "in_progress"
    | "success"
    | "failed"
    | "user_exists"
    | "invalid_data";
}

export const register = async (
  _: RegisterActionState,
  formData: FormData
): Promise<RegisterActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      username: formData.get("username"),
      password: formData.get("password"),
    });

    // const [user] = await getUser(validatedData.username);

    // if (user) {
    //   return { status: 'user_exists' } as RegisterActionState;
    // }
    // await createUser(validatedData.username, validatedData.password);
    await signIn("credentials", {
      username: validatedData.username,
      password: validatedData.password,
      redirect: false,
    });

    return { status: "success" };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: "invalid_data" };
    }

    return { status: "failed" };
  }
};
