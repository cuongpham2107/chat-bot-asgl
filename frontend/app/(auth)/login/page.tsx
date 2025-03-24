'use client';

import { useRouter } from 'next/navigation';
import { useActionState, useEffect, useState } from 'react';
import { toast } from '@/components/ui/toast';

import { AuthForm } from '@/components/site/auth/login-form';
import { SubmitButton } from '@/components/site/auth/submit-button';

import { login, type LoginActionState } from '../action';

export default function Page() {
  const router = useRouter();

  const [username, setUsername] = useState('');
  const [isSuccessful, setIsSuccessful] = useState(false);

  const [state, formAction] = useActionState<LoginActionState, FormData>(
    login,
    {
      status: 'idle',
    },
  );

  useEffect(() => {
    if (state.status === 'failed') {
      toast({
        type: 'error',
        description: 'Invalid credentials!',
      });
    } else if (state.status === 'invalid_data') {
      toast({
        type: 'error',
        description: 'Failed validating your submission!',
      });
    } else if (state.status === 'success') {
      setIsSuccessful(true);
      router.refresh();
    }
  }, [state.status, router]);

  const handleSubmit = (formData: FormData) => {
    setUsername(formData.get('username') as string);
    formAction(formData);
  };

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <h3 className="text-xl font-semibold dark:text-zinc-50">Đăng nhâp</h3>
          <p className="text-xs text-gray-500 dark:text-zinc-400">
            Sử dụng tài khoản và mật khẩu của bạn để đăng nhập
          </p>
        </div>
        <AuthForm action={handleSubmit} defaultEmail={username}>
          <SubmitButton isSuccessful={isSuccessful}>Đăng nhập</SubmitButton>
          {/* <p className="text-center text-sm text-gray-600 mt-4 dark:text-zinc-400">
            {"Don't have an account? "}
            <Link
              href="/register"
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Sign up
            </Link>
            {' for free.'}
          </p> */}
        </AuthForm>
      </div>
    </div>
  );
}
