import {
  createContext,
  useContext,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';

type RevueContextValue = {
  postings: string[];
  setPosting: (index: number, value: string) => void;
  addPosting: () => void;
  resumeFile: File | null;
  setResumeFile: (file: File | null) => void;
};

const RevueContext = createContext<RevueContextValue | undefined>(undefined);

export function RevueProvider({ children }: PropsWithChildren) {
  const [postings, setPostings] = useState<string[]>(['', '', '']);
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const value = useMemo<RevueContextValue>(
    () => ({
      postings,
      setPosting: (index, nextValue) => {
        setPostings((current) =>
          current.map((posting, currentIndex) =>
            currentIndex === index ? nextValue : posting,
          ),
        );
      },
      addPosting: () => {
        setPostings((current) => [...current, '']);
      },
      resumeFile,
      setResumeFile,
    }),
    [postings, resumeFile],
  );

  return <RevueContext.Provider value={value}>{children}</RevueContext.Provider>;
}

export function useRevue() {
  const context = useContext(RevueContext);

  if (!context) {
    throw new Error('useRevue must be used within a RevueProvider');
  }

  return context;
}