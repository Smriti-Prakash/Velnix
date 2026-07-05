export interface Invoice {
  id: string;
  invoice_number: string;
  vendor_name: string;
  invoice_amount: number;
  invoice_date: string;
  due_date?: string;
  purchase_order_number?: string;
  order_id?: string;
  payment_terms?: string;
  currency: string;
  risk_score: number;
  fraud_score: number;
  recommendation: 'APPROVE' | 'REVIEW' | 'INVESTIGATE' | 'REJECT';
  status: 'Pending' | 'Approved' | 'Rejected' | 'Review' | 'Investigate';
  priority: 'High' | 'Medium' | 'Low';
  risk_findings?: string[];
  fraud_findings?: string[];
  final_reasoning?: string;
  vendor_alerts?: string[];
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

export interface ErpVendor {
  vendor_id: number;
  vendor_name: string;
  vendor_status: 'Trusted' | 'Watchlist' | 'New' | 'Suspended';
  trust_score: number;
  average_invoice_amount: number;
  total_previous_invoices: number;
  previous_rejections: number;
  last_bank_account_change: string | null;
  bank_account: string | null;
  risk_level: 'Low' | 'Medium' | 'High';
}

export interface PurchaseOrder {
  purchase_order_number: string;
  vendor_id: number;
  vendor_name: string;
  approved_amount: number;
  currency: string;
  purchase_date: string;
  status: 'Open' | 'Cancelled' | 'Closed';
  expected_items: string;
}

export interface GoodsReceipt {
  goods_receipt_number: string;
  purchase_order_number: string;
  vendor_id: number;
  received_date: string;
  received_quantity: number;
  status: 'Complete' | 'Partial' | 'Pending';
}

export interface InvoiceHistoryRecord {
  id: number;
  invoice_number: string;
  vendor_id: number;
  vendor_name: string;
  invoice_amount: number;
  invoice_date: string;
  status: 'Paid' | 'Rejected' | 'Pending';
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
    if (!stored) return [];
    const parsed = JSON.parse(stored) as any[];
    return parsed.map(inv => {
      const invoice_number = inv.invoice_number || inv.invoiceNumber || inv.id || "INV-NEW";
      const vendor_name = inv.vendor_name || inv.vendorName || "Unknown";
      const invoice_amount = inv.invoice_amount !== undefined ? inv.invoice_amount : (inv.amount !== undefined ? inv.amount : 0);
      const invoice_date = inv.invoice_date || inv.invoiceDate || inv.date || new Date().toISOString().split("T")[0];
      const due_date = inv.due_date || inv.dueDate || invoice_date;
      const purchase_order_number = inv.purchase_order_number || inv.purchaseOrderNumber;
      const payment_terms = inv.payment_terms || inv.paymentTerms;
      const risk_score = inv.risk_score !== undefined ? inv.risk_score : (inv.riskScore !== undefined ? inv.riskScore : 0);
      const fraud_score = inv.fraud_score !== undefined ? inv.fraud_score : (inv.fraudScore !== undefined ? inv.fraudScore : 0);
      const recommendation = inv.recommendation || "REVIEW";
      const status = inv.status || "Pending";
      const priority = inv.priority || "Low";

      return {
        ...inv,
        id: invoice_number,
        invoice_number,
        vendor_name,
        invoice_amount,
        invoice_date,
        due_date,
        purchase_order_number,
        payment_terms,
        risk_score,
        fraud_score,
        recommendation,
        status,
        priority
      };
    });
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
    invoice_number: "INV-1002",
    vendor_name: "Acme Corp",
    invoice_amount: 10000.00,
    invoice_date: "2026-06-30",
    due_date: "2026-07-30",
    purchase_order_number: "PO-9912",
    payment_terms: "Net 30",
    currency: "$",
    risk_score: 5,
    fraud_score: 10,
    recommendation: "APPROVE",
    status: "Pending",
    priority: "Low",
    risk_findings: ["Vendor trust score is high (95/100).", "Transaction is within typical billing range."],
    fraud_findings: ["No duplicate invoices detected.", "No recent bank account changes."],
    final_reasoning: "Based on automated analysis, this invoice matches all transaction metadata, aligns with historical vendor averages, and contains zero duplicate or fraud indicators. Approved for immediate disbursement."
  },
  {
    id: "INV-2041",
    invoice_number: "INV-2041",
    vendor_name: "Delta Systems Ltd",
    invoice_amount: 85400.00,
    invoice_date: "2026-07-01",
    due_date: "2026-07-15",
    purchase_order_number: undefined,
    payment_terms: "Net 15",
    currency: "$",
    risk_score: 78,
    fraud_score: 65,
    recommendation: "INVESTIGATE",
    status: "Investigate",
    priority: "High",
    risk_findings: ["Invoice amount ($85,400.00) is 2.5x the historical average.", "Missing Purchase Order reference."],
    fraud_findings: ["Calculated fraud indicators exceed standard threshold.", "Vendor account flagged for review."],
    final_reasoning: "Caution recommended: The invoice deviates significantly from historical limits and is missing a PO reference. We recommend manual manager review before final AP approval."
  },
  {
    id: "INV-0883",
    invoice_number: "INV-0883",
    vendor_name: "Vertex Consulting",
    invoice_amount: 4500.00,
    invoice_date: "2026-06-28",
    due_date: "2026-07-28",
    purchase_order_number: "PO-4402",
    payment_terms: "Net 30",
    currency: "$",
    risk_score: 12,
    fraud_score: 8,
    recommendation: "APPROVE",
    status: "Approved",
    priority: "Low",
    risk_findings: ["Vendor trust score is verified.", "Matches PO reference."],
    fraud_findings: ["No anomalies detected."],
    final_reasoning: "Approved for disbursement. All verification checks passed."
  },
  {
    id: "INV-9941",
    invoice_number: "INV-9941",
    vendor_name: "Apex Logistics",
    invoice_amount: 12500.00,
    invoice_date: "2026-07-02",
    due_date: "2026-07-10",
    purchase_order_number: "PO-8120",
    payment_terms: "Due on Receipt",
    currency: "$",
    risk_score: 48,
    fraud_score: 42,
    recommendation: "REVIEW",
    status: "Review",
    priority: "Medium",
    risk_findings: ["Invoice is marked 'Due on Receipt'.", "Slight deviation from average amount."],
    fraud_findings: ["Urgent payment terms check recommended."],
    final_reasoning: "Under manual review due to urgent payment terms. Verify deliverables before releasing payment."
  },
  {
    id: "INV-7732",
    invoice_number: "INV-7732",
    vendor_name: "Sentinel Security",
    invoice_amount: 32000.00,
    invoice_date: "2026-06-25",
    due_date: "2026-07-25",
    purchase_order_number: undefined,
    payment_terms: "Net 30",
    currency: "$",
    risk_score: 92,
    fraud_score: 88,
    recommendation: "INVESTIGATE",
    status: "Rejected",
    priority: "High",
    risk_findings: ["Extreme deviation from historical average.", "No PO or contract reference."],
    fraud_findings: ["High indicator of potential overbilling.", "Security trust score is critical."],
    final_reasoning: "Transaction rejected. High risk indicators of potential overbilling and layout discrepancies."
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
