export default function StatCard({ value, label, accent = 'default' }: { value: string; label: string; accent?: 'default' | 'green' | 'violet' }) {
  return <div className={`stat-card ${accent}`}><strong>{value}</strong><span>{label}</span></div>;
}
