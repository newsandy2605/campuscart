import '../styles.css';

export const metadata = {
  title: 'CampusCart — Your campus. Your marketplace.',
  description: 'A verified campus marketplace for buying, selling and swapping student goods.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
