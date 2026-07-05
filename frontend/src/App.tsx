import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/common/Layout';
import { Dashboard } from './pages/Dashboard';
import { ApprovalQueue } from './pages/ApprovalQueue';
import { AllInvoices } from './pages/AllInvoices';
import { InvoiceDetails } from './pages/InvoiceDetails';
import { Upload } from './pages/Upload';
import { Vendors } from './pages/Vendors';
import { VendorDetails } from './pages/VendorDetails';
import { PurchaseOrders } from './pages/PurchaseOrders';
import { PODetails } from './pages/PODetails';
import { GoodsReceipts } from './pages/GoodsReceipts';
import { GRDetails } from './pages/GRDetails';
import { Analytics } from './pages/Analytics';
import { AuditLogs } from './pages/AuditLogs';
import { Settings } from './pages/Settings';
import { DevModeProvider } from './context/DevModeContext';

function App() {
  return (
    <DevModeProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/queue" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/queue" element={<ApprovalQueue />} />
          <Route path="/invoices" element={<AllInvoices />} />
          <Route path="/invoices/:id" element={<InvoiceDetails />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/vendors/:name" element={<VendorDetails />} />
          <Route path="/purchase-orders" element={<PurchaseOrders />} />
          <Route path="/purchase-orders/:poNumber" element={<PODetails />} />
          <Route path="/goods-receipts" element={<GoodsReceipts />} />
          <Route path="/goods-receipts/:grnNumber" element={<GRDetails />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/audit" element={<AuditLogs />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </DevModeProvider>
  );
}

export default App;

