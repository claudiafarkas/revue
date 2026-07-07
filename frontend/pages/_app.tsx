import type { AppProps } from 'next/app';
import { RevueProvider } from '../src/context/RevueContext';
import { AuthProvider } from '../src/context/AuthContext';
import { SiteFrame } from '../src/components/SiteFrame';
import '../src/styles/global.css';

export default function RevueApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <RevueProvider>
        <SiteFrame>
          <Component {...pageProps} />
        </SiteFrame>
      </RevueProvider>
    </AuthProvider>
  );
}