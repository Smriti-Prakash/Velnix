export interface Invoice {
  id: string;
  vendorName: string;
  amount: number;
  date: string;
  dueDate: string;
  purchaseOrderNumber?: string;
  paymentTerms?: string;
  currency: string;
  riskScore: number;
  fraudScore: number;
  recommendation: 'APPROVE' | 'REVIEW' | 'INVESTIGATE';
  status: 'Pending' | 'Approved' | 'Rejected' | 'Review' | 'Investigate';
  priority: 'High' | 'Medium' | 'Low';
  invoiceDate: string;
}

export interface Vendor {
  name: string;
  status: 'Trusted' | 'Watchlist' | 'New';
  trustScore: number;
  previousInvoicesCount: number;
  averageInvoiceAmount: number;
  previousRejections: number;
  lastBankAccountChange: string;
  riskLevel: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface AuditLog {
  timestamp: string;
  invoiceNumber: string;
  agent: string;
  sessionId: string;
  userRole: string;
  decision: string;
  recommendation: string;
  reason: string;
}

const LOCAL_INVOICES_KEY = "velnix_custom_invoices";
const LOCAL_VENDORS_KEY = "velnix_custom_vendors";

const getStoredInvoices = (): Invoice[] => {
  try {
    const stored = localStorage.getItem(LOCAL_INVOICES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

const getStoredVendors = (): Vendor[] => {
  try {
    const stored = localStorage.getItem(LOCAL_VENDORS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const addCustomInvoice = (inv: Invoice) => {
  const stored = getStoredInvoices();
  if (!stored.some(i => i.id === inv.id)) {
    const updated = [inv, ...stored];
    localStorage.setItem(LOCAL_INVOICES_KEY, JSON.stringify(updated));
    MOCK_INVOICES.unshift(inv);
  }
};

export const addCustomVendor = (vendor: Vendor) => {
  const stored = getStoredVendors();
  if (!stored.some(v => v.name === vendor.name)) {
    const updated = [vendor, ...stored];
    localStorage.setItem(LOCAL_VENDORS_KEY, JSON.stringify(updated));
    MOCK_VENDORS.unshift(vendor);
  }
};

export const MOCK_INVOICES: Invoice[] = [
  ...getStoredInvoices(),
  {
    id: "INV-1002",
    vendorName: "Acme Corp",
    amount: 10000.00,
    date: "2026-06-30",
    dueDate: "2026-07-30",
    purchaseOrderNumber: "PO-9912",
    paymentTerms: "Net 30",
    currency: "$",
    riskScore: 5,
    fraudScore: 10,
    recommendation: "APPROVE",
    status: "Pending",
    priority: "Low",
    invoiceDate: "2026-06-30"
  },
  {
    id: "INV-2041",
    vendorName: "Delta Systems Ltd",
    amount: 85400.00,
    date: "2026-07-01",
    dueDate: "2026-07-15",
    purchaseOrderNumber: undefined,
    paymentTerms: "Net 15",
    currency: "$",
    riskScore: 78,
    fraudScore: 65,
    recommendation: "INVESTIGATE",
    status: "Investigate",
    priority: "High",
    invoiceDate: "2026-07-01"
  },
  {
    id: "INV-0883",
    vendorName: "Vertex Consulting",
    amount: 4500.00,
    date: "2026-06-28",
    dueDate: "2026-07-28",
    purchaseOrderNumber: "PO-4402",
    paymentTerms: "Net 30",
    currency: "$",
    riskScore: 12,
    fraudScore: 8,
    recommendation: "APPROVE",
    status: "Approved",
    priority: "Low",
    invoiceDate: "2026-06-28"
  },
  {
    id: "INV-9941",
    vendorName: "Apex Logistics",
    amount: 12500.00,
    date: "2026-07-02",
    dueDate: "2026-07-10",
    purchaseOrderNumber: "PO-8120",
    paymentTerms: "Due on Receipt",
    currency: "$",
    riskScore: 48,
    fraudScore: 42,
    recommendation: "REVIEW",
    status: "Review",
    priority: "Medium",
    invoiceDate: "2026-07-02"
  },
  {
    id: "INV-7732",
    vendorName: "Sentinel Security",
    amount: 32000.00,
    date: "2026-06-25",
    dueDate: "2026-07-25",
    purchaseOrderNumber: undefined,
    paymentTerms: "Net 30",
    currency: "$",
    riskScore: 92,
    fraudScore: 88,
    recommendation: "INVESTIGATE",
    status: "Rejected",
    priority: "High",
    invoiceDate: "2026-06-25"
  }
];

export const MOCK_VENDORS: Vendor[] = [
  ...getStoredVendors(),
  {
    name: "Acme Corp",
    status: "Trusted",
    trustScore: 95,
    previousInvoicesCount: 150,
    averageInvoiceAmount: 5000.00,
    previousRejections: 1,
    lastBankAccountChange: "2025-12-01",
    riskLevel: "Low"
  },
  {
    name: "Delta Systems Ltd",
    status: "Watchlist",
    trustScore: 45,
    previousInvoicesCount: 12,
    averageInvoiceAmount: 42000.00,
    previousRejections: 3,
    lastBankAccountChange: "2026-05-14",
    riskLevel: "High"
  },
  {
    name: "Vertex Consulting",
    status: "Trusted",
    trustScore: 98,
    previousInvoicesCount: 84,
    averageInvoiceAmount: 3800.00,
    previousRejections: 0,
    lastBankAccountChange: "2024-08-20",
    riskLevel: "Low"
  },
  {
    name: "Apex Logistics",
    status: "New",
    trustScore: 70,
    previousInvoicesCount: 2,
    averageInvoiceAmount: 11000.00,
    previousRejections: 0,
    lastBankAccountChange: "2026-06-01",
    riskLevel: "Medium"
  },
  {
    name: "Sentinel Security",
    status: "Watchlist",
    trustScore: 30,
    previousInvoicesCount: 8,
    averageInvoiceAmount: 30000.00,
    previousRejections: 2,
    lastBankAccountChange: "2026-06-20",
    riskLevel: "Critical"
  }
];

export const MOCK_AUDIT_LOGS: AuditLog[] = [
  {
    timestamp: "2026-07-02T18:22:58.580Z",
    invoiceNumber: "INV-1002",
    agent: "Velnix Platform",
    sessionId: "session-xyz",
    userRole: "Finance Analyst",
    decision: "SUCCESS",
    recommendation: "APPROVE",
    reason: "Low risk profile, matched PO and trusted historical record."
  },
  {
    timestamp: "2026-07-01T15:10:42.021Z",
    invoiceNumber: "INV-2041",
    agent: "Velnix Platform",
    sessionId: "session-abc",
    userRole: "Finance Manager",
    decision: "SUCCESS",
    recommendation: "INVESTIGATE",
    reason: "High risk due to Watchlist vendor status, recent bank details change, and missing PO."
  },
  {
    timestamp: "2026-06-30T10:04:12.330Z",
    invoiceNumber: "INV-0883",
    agent: "Velnix Platform",
    sessionId: "session-def",
    userRole: "Finance Analyst",
    decision: "SUCCESS",
    recommendation: "APPROVE",
    reason: "Highly trusted vendor profile, matched PO."
  }
];

export const MOCK_CFO_BRIEF = 
  "Today's Accounts Payable situation is stable but requires action on key exceptions. We currently have 2 invoices pending approval in the queue totaling $95,400. One high-risk alert has been flagged for Delta Systems Ltd (INV-2041) due to a critical risk score of 78/100, combined with a recent bank account change and a missing Purchase Order. All other regular vendor transactions are performing within normal parameters. We recommend immediate investigation on INV-2041 before authorization.";
