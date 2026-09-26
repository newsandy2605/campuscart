import AppShell from '../../../components/AppShell';
import ListingDetailClient from '../../../components/ListingDetailClient';
import { getListing } from '../../../lib/api';
export default async function ListingPage({ params }: { params: Promise<{ id: string }> }) { const { id }=await params; const listing=await getListing(id); return <AppShell active="Marketplace"><ListingDetailClient listing={listing}/></AppShell>; }
