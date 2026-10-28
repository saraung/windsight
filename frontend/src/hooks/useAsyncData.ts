import { useEffect, useState } from 'react';

interface AsyncState<T> {
  key: string;
  data: T | null;
  error: string | null;
}

export function useAsyncData<T>(key: string, loader: () => Promise<T>) {
  const [state, setState] = useState<AsyncState<T>>({ key: '', data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    const requestKey = key;

    loader()
      .then((data) => {
        if (!cancelled) setState({ key: requestKey, data, error: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            key: requestKey,
            data: null,
            error: error instanceof Error ? error.message : 'Request failed',
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [key, loader]);

  const isCurrent = state.key === key;
  return {
    data: state.data,
    error: isCurrent ? state.error : null,
    loading: !isCurrent,
  };
}
