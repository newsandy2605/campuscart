'use client';
import { useEffect, useState } from 'react';
import { createListing, getAddresses, getCampus, getCampusSlug, getCourses, getListingCopilot, getPriceInsight, uploadListingImage, type Address, type Campus } from '../lib/api';

const steps = ['Photos', 'Details', 'Price', 'Pickup', 'Review'];
const MAX_PHOTOS = 6;
type Course = { id:number; code:string; name:string; semester:string };

export default function ListingWizard() {
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Academic Supplies');
  const [condition, setCondition] = useState('good');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');
  const [listingType, setListingType] = useState('sell');
  const [pickupArea, setPickupArea] = useState('');
  const [landmark, setLandmark] = useState('');
  const [pickupInstructions, setPickupInstructions] = useState('');
  const [addressId, setAddressId] = useState('');
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [campus, setCampus] = useState<Campus | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourses, setSelectedCourses] = useState<number[]>([]);
  const [photos, setPhotos] = useState<{ url: string; alt: string; name: string }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [copilot, setCopilot] = useState<{ suggested_title: string; category: string; detected_attributes: string[] } | null>(null);
  const [priceInsight, setPriceInsight] = useState<{ sample_size: number; low: number | null; median: number | null; high: number | null } | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [published, setPublished] = useState(false);

  useEffect(() => {
    const slug = getCampusSlug();
    if (!slug) return;
    Promise.all([getAddresses(), getCampus(slug), getCourses(slug)]).then(([as, c, cs]) => {
      setAddresses(as); setCampus(c); setCourses(cs);
      setPickupArea(c.pickup_locations?.[0]?.name || '');
      setLandmark(c.pickup_locations?.[0]?.landmark || '');
      setAddressId(String(as.find((x) => x.is_default)?.id || ''));
    }).catch((e) => setError(e instanceof Error ? e.message : 'Unable to load listing options'));
  }, []);

  useEffect(() => {
    if (step !== 2 || !getCampusSlug()) return;
    getPriceInsight(getCampusSlug(), category).then(setPriceInsight).catch(() => setPriceInsight(null));
  }, [step, category]);

  const next = () => {
    if (step === 0 && photos.length === 0) { setError('Add at least one photo so buyers can see the item.'); return; }
    setError(''); setStep((s) => Math.min(4, s + 1));
  };

  const handlePhotos = async (files: FileList | null) => {
    if (!files?.length) return;
    setError('');
    const selected = Array.from(files).slice(0, MAX_PHOTOS - photos.length);
    if (!selected.length) return;
    setUploading(true);
    try {
      const uploaded: { url: string; alt: string; name: string }[] = [];
      for (const file of selected) uploaded.push({ ...(await uploadListingImage(file)), alt: title || file.name, name: file.name });
      setPhotos((current) => [...current, ...uploaded].slice(0, MAX_PHOTOS));
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to upload photos'); }
    finally { setUploading(false); }
  };

  const removePhoto = (index: number) => setPhotos((current) => current.filter((_, i) => i !== index));
  const toggleCourse = (id: number) => setSelectedCourses((current) => current.includes(id) ? current.filter((x) => x !== id) : [...current, id]);
  const runCopilot = async () => {
    setBusy(true); setError('');
    try { setCopilot(await getListingCopilot({ title, description, category, condition })); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to generate listing suggestions'); }
    finally { setBusy(false); }
  };

  const publish = async () => {
    setBusy(true); setError('');
    try {
      if (!photos.length) throw new Error('Add at least one listing photo');
      if (listingType !== 'giveaway' && Number(price) < 0) throw new Error('Price cannot be negative');
      await createListing({
        campus_slug: getCampusSlug(), title: title || copilot?.suggested_title || 'Campus Listing', category: copilot?.category || category,
        condition, listing_type: listingType, price: listingType === 'giveaway' ? 0 : Number(price), description,
        pickup_location_id: pickupArea ? campus?.pickup_locations?.find((x) => x.name === pickupArea)?.id : undefined,
        pickup_address_id: addressId ? Number(addressId) : undefined, pickup_area: pickupArea, pickup_landmark: landmark,
        pickup_instructions: pickupInstructions, course_ids: selectedCourses,
        images: photos.map((photo, index) => ({ url: photo.url, alt: photo.alt, sort_order: index })),
      });
      setPublished(true);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to publish listing'); }
    finally { setBusy(false); }
  };

  if (published) return <div className="wizard"><div className="wizard-panel"><div className="verified-badge">✓ Listing published</div><h2>{title || 'Your listing'} is live.</h2><p className="muted">Buyers in your verified campus can now discover it.</p><a className="btn btn-primary" href="/seller">Open Seller Studio →</a></div></div>;

  return <div className="wizard">
    <div className="wizard-steps">{steps.map((s, i) => <div key={s} className={i === step ? 'wizard-step current' : i < step ? 'wizard-step done' : 'wizard-step'}><span>{i < step ? '✓' : i + 1}</span>{s}</div>)}</div>
    <div className="wizard-panel">
      {step === 0 && <>
        <div className="eyebrow">STEP 1</div><h2>Show the actual item</h2>
        <label className="upload-box" style={{ cursor: uploading || photos.length >= MAX_PHOTOS ? 'default' : 'pointer' }}>
          <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden disabled={uploading || photos.length >= MAX_PHOTOS} onChange={(e) => { void handlePhotos(e.target.files); e.currentTarget.value = ''; }} />
          <div className="upload-mark">{uploading ? '…' : '＋'}</div><strong>{uploading ? 'Uploading photos…' : photos.length >= MAX_PHOTOS ? 'Photo limit reached' : 'Add photos'}</strong><span>Choose files from your laptop · JPEG, PNG, WebP or GIF · up to 5 MB each · {MAX_PHOTOS} max</span>
        </label>
        {photos.length > 0 && <div className="photo-strip">{photos.map((photo, index) => <div key={`${photo.url}-${index}`} style={{ position: 'relative' }}><img src={photo.url} alt={photo.alt} /><button type="button" aria-label={`Remove ${photo.name}`} className="btn btn-ghost" style={{ position: 'absolute', right: 4, top: 4, padding: '3px 7px' }} onClick={() => removePhoto(index)}>×</button></div>)}</div>}
        {photos.length > 0 && <div className="hint">{photos.length} photo{photos.length === 1 ? '' : 's'} added. The first photo is the listing thumbnail.</div>}
      </>}

      {step === 1 && <>
        <div className="eyebrow">STEP 2</div><h2>Tell buyers about it</h2>
        <div className="form-grid">
          <label>Title<input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Casio Scientific Calculator" /></label>
          <label>Category<select value={category} onChange={(e) => setCategory(e.target.value)}><option>Academic Supplies</option><option>Books</option><option>Electronics</option><option>Furniture</option><option>Clothing</option><option>Hostel Essentials</option></select></label>
          <label>Condition<select value={condition} onChange={(e) => setCondition(e.target.value)}><option value="new">New</option><option value="like-new">Like new</option><option value="good">Good</option><option value="fair">Fair</option></select></label>
          <label>Listing type<select value={listingType} onChange={(e) => setListingType(e.target.value)}><option value="sell">Sell</option><option value="rent">Rent</option><option value="giveaway">Give away</option></select></label>
          <label className="span-2">Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Mention condition, usage, included items and anything a buyer should know." /></label>
        </div>
        {courses.length > 0 && <div className="panel" style={{ marginTop: 14, padding: 14 }}><div className="eyebrow">COURSE TAGS</div><strong>Relevant courses</strong><p className="muted small">Tag this listing so students in the course can find it.</p><div className="category-row">{courses.map(c => <button type="button" key={c.id} className={selectedCourses.includes(c.id) ? 'category-chip active' : 'category-chip'} onClick={() => toggleCourse(c.id)}>{c.code}</button>)}</div></div>}
        <div className="copilot"><div><strong>Listing Copilot</strong><span>Creates structured suggestions from what you entered.</span>{copilot?.detected_attributes?.length ? <small>{copilot.detected_attributes.join(' · ')}</small> : null}</div><button type="button" className="btn btn-soft" onClick={runCopilot} disabled={busy}>{busy ? 'Thinking...' : 'Suggest details'}</button></div>
        {copilot && <div className="success-box">Suggested title: <strong>{copilot.suggested_title}</strong><br />Suggested category: <strong>{copilot.category}</strong><button type="button" className="btn btn-soft" style={{ marginLeft: 10 }} onClick={() => { setTitle(copilot.suggested_title); setCategory(copilot.category); }}>Use suggestions</button></div>}
      </>}

      {step === 2 && <>
        <div className="eyebrow">STEP 3</div><h2>Choose a fair price</h2>
        {listingType === 'giveaway' ? <div className="success-box">This listing will be free for buyers.</div> : <><div className="price-preview"><div><span>Campus range</span><strong>{priceInsight?.low != null && priceInsight?.high != null ? `₹${priceInsight.low} – ₹${priceInsight.high}` : 'Calculating...'}</strong></div><div><span>Typical accepted</span><strong>{priceInsight?.median != null ? `₹${priceInsight.median}` : '—'}</strong></div></div><label>Listing price<input inputMode="numeric" value={price} onChange={(e) => setPrice(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="400" /></label><div className="hint">Pricing uses completed-sale data where available.</div></>}
      </>}

      {step === 3 && <>
        <div className="eyebrow">STEP 4</div><h2>Choose a safe pickup method</h2>
        <div className="form-grid">
          <label>Campus pickup point<select value={pickupArea} onChange={(e) => { setPickupArea(e.target.value); const p=campus?.pickup_locations?.find(x=>x.name===e.target.value); if(p) setLandmark(p.landmark); }}><option value="">Select a campus point</option>{campus?.pickup_locations?.map((p) => <option key={p.id} value={p.name}>{p.name}</option>)}</select></label>
          <label>Landmark<input value={landmark} onChange={(e) => setLandmark(e.target.value)} /></label>
          <label>Saved address<select value={addressId} onChange={(e) => setAddressId(e.target.value)}><option value="">No private address</option>{addresses.map((a) => <option key={a.id} value={a.id}>{a.label} · {a.locality}, {a.city}</option>)}</select></label>
          <label className="span-2">Pickup instructions<textarea value={pickupInstructions} onChange={(e) => setPickupInstructions(e.target.value)} placeholder="Example: call when you reach the north gate." maxLength={500} /></label>
        </div>
      </>}

      {step === 4 && <>
        <div className="eyebrow">STEP 5</div><h2>Review before publishing</h2>
        <div className="detail-meta"><span className="soft-tag">{category}</span><span className="soft-tag">{condition.replace('-', ' ')}</span><span className="soft-tag">{listingType}</span>{selectedCourses.map(id => <span className="soft-tag" key={id}>{courses.find(c=>c.id===id)?.code}</span>)}</div>
        <div className="review-grid"><div><strong>{title || copilot?.suggested_title || 'Campus listing'}</strong><p>{description || 'No description provided.'}</p></div><div><strong>{listingType==='giveaway'?'Free':`₹${Number(price || 0).toLocaleString('en-IN')}`}</strong><p>{pickupArea || 'Campus pickup'}{landmark ? ` · ${landmark}` : ''}</p></div></div>
      </>}
      {error && <div className="error-box" style={{ marginTop: 12 }}>{error}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 20 }}>{step > 0 ? <button className="btn btn-ghost" onClick={() => setStep(s => s - 1)}>← Back</button> : <span/>}{step < 4 ? <button className="btn btn-primary" disabled={uploading} onClick={next}>Next →</button> : <button className="btn btn-primary" disabled={busy || uploading} onClick={publish}>{busy ? 'Publishing...' : 'Publish listing'}</button>}</div>
    </div>
  </div>;
}
