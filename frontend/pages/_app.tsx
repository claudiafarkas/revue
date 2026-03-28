import type { AppProps } from 'next/app';
import { RevueProvider } from '../src/context/RevueContext';
import { SiteFrame } from '../src/components/SiteFrame';
import '../src/styles/global.css';

export default function RevueApp({ Component, pageProps }: AppProps) {
  return (
    <RevueProvider>
      <SiteFrame>
        <Component {...pageProps} />
      </SiteFrame>
    </RevueProvider>
  );
}