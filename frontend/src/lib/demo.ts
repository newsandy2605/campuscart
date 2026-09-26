export type Product = {
  id: string;
  name: string;
  price: number;
  category: string;
  condition: string;
  campus: string;
  location: string;
  distance: string;
  seller: string;
  sellerRating: number;
  verified: boolean;
  created: string;
  image: string;
  description: string;
  course?: string;
  negotiable?: boolean;
  views?: number;
  saves?: number;
};

export const products: Product[] = [
  { id: '1', name: 'Engineering Mathematics', price: 450, category: 'Books', condition: 'Good', campus: 'Demo Campus University', location: 'Main Library', distance: '0.3 km', seller: 'Alex Verma', sellerRating: 4.8, verified: true, created: '3 min ago', image: '/products/math.svg', description: 'Second edition textbook with clean pages and light highlighting. Useful for first-year engineering students.', course: 'Engineering Mathematics', negotiable: true, views: 34, saves: 8 },
  { id: '2', name: 'Scientific Calculator', price: 380, category: 'Academic Supplies', condition: 'Good', campus: 'Demo Campus University', location: 'Hostel A', distance: '0.7 km', seller: 'Priya Shah', sellerRating: 4.9, verified: true, created: '11 min ago', image: '/products/calculator.svg', description: 'Fully working scientific calculator. Battery replaced recently.', course: 'Engineering Mathematics', negotiable: true, views: 52, saves: 13 },
  { id: '3', name: 'iPhone 12', price: 22000, category: 'Electronics', condition: 'Good', campus: 'Demo Campus University', location: 'Main Gate', distance: '1.1 km', seller: 'Rahul Mehta', sellerRating: 4.6, verified: true, created: '18 min ago', image: '/products/phone.svg', description: '128 GB model in good working condition. Includes case and charging cable.', negotiable: false, views: 81, saves: 19 },
  { id: '4', name: 'Hostel Study Chair', price: 1200, category: 'Hostel Essentials', condition: 'Good', campus: 'Demo Campus University', location: 'Hostel B', distance: '0.9 km', seller: 'Sneha Iyer', sellerRating: 4.7, verified: true, created: '26 min ago', image: '/products/chair.svg', description: 'Compact study chair suitable for hostel rooms. Minor cosmetic marks.', negotiable: true, views: 29, saves: 7 },
  { id: '5', name: 'MacBook Air M1', price: 42000, category: 'Electronics', condition: 'Like new', campus: 'Demo Campus University', location: 'Kothrud', distance: '3.2 km', seller: 'Karan Patel', sellerRating: 4.9, verified: true, created: '1 hour ago', image: '/products/laptop.svg', description: 'M1 MacBook Air with excellent battery health. Original charger included.', negotiable: false, views: 76, saves: 22 },
  { id: '6', name: 'Lab Coat', price: 500, category: 'Clothing', condition: 'Good', campus: 'Demo Campus University', location: 'Hostel C', distance: '1.2 km', seller: 'Aditi Rao', sellerRating: 4.5, verified: true, created: '2 hours ago', image: '/products/coat.svg', description: 'Standard lab coat, lightly used and freshly washed.', course: 'Engineering Lab', negotiable: true, views: 18, saves: 4 },
  { id: '7', name: 'Study Table', price: 1500, category: 'Furniture', condition: 'Good', campus: 'Demo Campus University', location: 'Hostel B', distance: '0.8 km', seller: 'Arjun Patel', sellerRating: 4.7, verified: true, created: '2 hours ago', image: '/products/table.svg', description: 'Wooden study table with one drawer. Pickup only.', negotiable: true, views: 44, saves: 11 },
  { id: '8', name: 'Wireless Earbuds', price: 1100, category: 'Electronics', condition: 'Like new', campus: 'Demo Campus University', location: 'Student Centre', distance: '0.4 km', seller: 'Neha Kapoor', sellerRating: 4.8, verified: true, created: '3 hours ago', image: '/products/earbuds.svg', description: 'Used only a handful of times. Includes charging case.', negotiable: true, views: 38, saves: 10 },
];

export const campus = {
  id: 1,
  name: 'Demo Campus University',
  slug: 'demo-campus',
  city: 'Pune, Maharashtra',
  emailDomain: 'student.example.edu',
  members: 1254,
  description: 'A student-first campus marketplace for books, electronics, academic supplies, hostel essentials, and more.',
};

export const wantedPosts = [
  { id: 1, title: 'DBMS textbook', budget: '₹300–₹500', neededBy: 'Sep 30', interested: 17, category: 'Books' },
  { id: 2, title: '24-inch monitor', budget: '₹3,000–₹5,000', neededBy: 'Oct 4', interested: 9, category: 'Electronics' },
  { id: 3, title: 'Scientific calculator', budget: '₹350–₹450', neededBy: 'Sep 28', interested: 27, category: 'Academic Supplies' },
  { id: 4, title: 'Lab coat', budget: 'Up to ₹600', neededBy: 'Oct 2', interested: 11, category: 'Clothing' },
];

export const conversations = [
  { id: 1, seller: 'Alex Verma', listing: 'Engineering Mathematics', time: '2m', preview: 'Can pick it up tomorrow around 5?', image: '/products/math.svg' },
  { id: 2, seller: 'Priya Shah', listing: 'Scientific Calculator', time: '15m', preview: 'Yes, it is available.', image: '/products/calculator.svg' },
  { id: 3, seller: 'Rohit Mehta', listing: 'Monitor', time: '1h', preview: 'Would you take ₹4,200?', image: '/products/laptop.svg' },
  { id: 4, seller: 'Sneha Iyer', listing: 'Hostel Chair', time: '3h', preview: 'Sure. We can meet at the library.', image: '/products/chair.svg' },
];

export const demandData = [
  { name: 'Calculators', wanted: 42, supply: 8, trend: '+18%', range: '₹350–₹550' },
  { name: 'DBMS Books', wanted: 27, supply: 9, trend: '+11%', range: '₹300–₹500' },
  { name: 'Monitors', wanted: 18, supply: 5, trend: '+8%', range: '₹3,000–₹6,000' },
  { name: 'Lab Coats', wanted: 11, supply: 4, trend: '+5%', range: '₹350–₹600' },
  { name: 'Study Tables', wanted: 9, supply: 7, trend: '+3%', range: '₹1,000–₹1,800' },
];

export const swapMatches = [
  { person: 'Alex Verma', have: 'Engineering Mathematics', want: 'Scientific Calculator', score: 87, image: '/products/math.svg' },
  { person: 'Priya Shah', have: 'Engineering Mathematics', want: 'Monitor', score: 76, image: '/products/calculator.svg' },
  { person: 'Rahul Mehta', have: 'Monitor', want: 'Calculator', score: 70, image: '/products/laptop.svg' },
];

export const notifications = [
  { type: 'offer', title: 'Alex accepted your ₹400 offer', time: '2 min ago' },
  { type: 'payment', title: 'Payment received for Engineering Mathematics', time: '8 min ago' },
  { type: 'wanted', title: 'New match for your calculator request', time: '18 min ago' },
  { type: 'message', title: 'Priya sent you a message', time: '32 min ago' },
  { type: 'listing', title: 'Your listing received 12 new views', time: '1 hr ago' },
  { type: 'swap', title: 'You have a new 87% swap match', time: '2 hr ago' },
];
