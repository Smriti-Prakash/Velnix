import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertTriangle, Copy, Download } from 'lucide-react';
import { addCustomInvoice, addCustomVendor } from '../services/mockData';
import type { Invoice, Vendor } from '../services/mockData';

const mapToInvoice = (
  invoiceData: any,
  riskAssessment: any,
  fraudAssessment: any
): Invoice => {
  const id = invoiceData.invoice_number || "INV-NEW";
  const vendorName = invoiceData.vendor_name || "Unknown";
  const amount = invoiceData.invoice_amount || 0;
  const date = invoiceData.invoice_date || new Date().toISOString().split("T")[0];
  const dueDate = invoiceData.due_date || date;
  const riskScore = riskAssessment?.risk_score ?? 0;
  const fraudScore = fraudAssessment?.fraud_score ?? 0;
  const recommendation = (riskAssessment?.recommendation ?? "REVIEW") as 'APPROVE' | 'REVIEW' | 'INVESTIGATE';

  let status: Invoice['status'] = 'Pending';
  if (recommendation === 'APPROVE') status = 'Pending';
  else if (recommendation === 'REVIEW') status = 'Review';
  else if (recommendation === 'INVESTIGATE') status = 'Investigate';

  let priority: Invoice['priority'] = 'Low';
  if (riskScore > 75 || fraudScore > 75) priority = 'High';
  else if (riskScore > 40 || fraudScore > 40) priority = 'Medium';

  return {
    id,
    vendorName,
    amount,
    date,
    dueDate,
    purchaseOrderNumber: invoiceData.purchase_order_number || undefined,
    paymentTerms: invoiceData.payment_terms || undefined,
    currency: invoiceData.currency || "$",
    riskScore,
    fraudScore,
    recommendation,
    status,
    priority,
    invoiceDate: date
  };
};

const mapToVendor = (vendorProfile: any, riskAssessment: any): Vendor => {
  const riskScore = riskAssessment?.risk_score ?? 0;
  let riskLevel: Vendor['riskLevel'] = 'Low';
  if (riskScore > 85) riskLevel = 'Critical';
  else if (riskScore > 60) riskLevel = 'High';
  else if (riskScore > 30) riskLevel = 'Medium';

  return {
    name: vendorProfile.vendor_name || "Unknown",
    status: (vendorProfile.vendor_status || "New") as any,
    trustScore: vendorProfile.trust_score ?? 70,
    previousInvoicesCount: vendorProfile.total_previous_invoices ?? 0,
    averageInvoiceAmount: vendorProfile.average_invoice_amount ?? 0,
    previousRejections: vendorProfile.previous_rejections ?? 0,
    lastBankAccountChange: vendorProfile.last_bank_account_change || "N/A",
    riskLevel: riskLevel
  };
};

export const Upload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [finalInvoiceId, setFinalInvoiceId] = useState<string>("INV-1002");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    "Uploading document to server...",
    "Extracting metadata fields...",
    "Verifying historical vendor profile...",
    "Evaluating risk score penalties...",
    "Scanning for duplicate fraud indicators...",
    "Compiling final report..."
  ];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (validTypes.includes(file.type)) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError("Unsupported file type. Please upload a PDF, PNG, or JPEG.");
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (validTypes.includes(file.type)) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError("Unsupported file type. Please upload a PDF, PNG, or JPEG.");
      }
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;
    
    setStatus('processing');
    setCurrentStep(0);
    setError(null);
    setReport('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errMsg = "Upload failed.";
        try {
          const errObj = JSON.parse(errorText);
          errMsg = errObj.detail || errObj.message || errMsg;
        } catch {
          errMsg = errorText || errMsg;
        }
        throw new Error(errMsg);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Failed to initialize progress stream.");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Normalize CRLF to LF to handle Windows line endings
        const normalized = buffer.replace(/\r\n/g, '\n');
        const parts = normalized.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          const lines = part.split('\n');
          let data = "";
          let event = "";

          for (const line of lines) {
            if (line.startsWith('event:')) {
              event = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              data = line.replace('data:', '').trim();
            }
          }

          if (event === "error") {
            try {
              const parsed = JSON.parse(data);
              throw new Error(parsed.message || "Orchestrator pipeline execution failed.");
            } catch (e: any) {
              throw new Error(e.message || "Orchestrator pipeline execution failed.");
            }
          }

          if (data) {
            try {
              const parsed = JSON.parse(data);
              const { step, report: finalReport, invoice_data, vendor_profile, risk_assessment, fraud_assessment } = parsed;

              if (step === "upload_complete") {
                setCurrentStep(1);
              } else if (step === "document_extraction") {
                setCurrentStep(2);
              } else if (step === "invoice_analysis") {
                setCurrentStep(3);
              } else if (step === "vendor_intelligence") {
                setCurrentStep(4);
              } else if (step === "risk_assessment") {
                setCurrentStep(5);
              } else if (step === "fraud_intelligence") {
                setCurrentStep(5);
              } else if (step === "final_decision") {
                setCurrentStep(5);
              } else if (step === "report_ready") {
                setReport(finalReport);
                setStatus('done');

                if (invoice_data && Object.keys(invoice_data).length > 0) {
                  const customInv = mapToInvoice(invoice_data, risk_assessment, fraud_assessment);
                  setFinalInvoiceId(customInv.id);
                  addCustomInvoice(customInv);

                  if (vendor_profile && Object.keys(vendor_profile).length > 0) {
                    const customVendor = mapToVendor(vendor_profile, risk_assessment);
                    addCustomVendor(customVendor);
                  }
                } else {
                  // Fallback to regex if for some reason the tools weren't executed
                  let parsedId = "INV-NEW";
                  const invNumMatch = finalReport.match(/(?:Invoice Number|invoice_number)\s*[:"\s]\s*([a-zA-Z0-9-]+)/i);
                  if (invNumMatch) {
                    parsedId = invNumMatch[1].trim();
                  }
                  setFinalInvoiceId(parsedId);
                }
              }
            } catch (e) {
              console.error("Error processing event data:", e);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during analysis.");
      setStatus('idle');
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setStatus('idle');
    setCurrentStep(0);
    setError(null);
    setReport('');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Velnix-Investigation-Report-${finalInvoiceId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-xl border border-slate-200 shadow-sm p-8 space-y-8 animate-fadeIn">
      <div className="flex flex-col space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Upload Vendor Invoice</h2>
          <p className="text-xs text-slate-500 mt-1">Submit documents for automated metadata extraction and multi-agent risk screening</p>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 flex items-start space-x-3 text-sm text-rose-800 animate-fadeIn">
            <AlertTriangle className="h-5 w-5 text-rose-600 mt-0.5 shrink-0" />
            <div className="space-y-2">
              <p className="font-bold text-rose-900">Analysis Process Interrupted</p>
              <p className="text-xs text-rose-700 leading-relaxed">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  startAnalysis();
                }}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold transition-colors shadow-sm cursor-pointer"
              >
                Retry Analysis
              </button>
            </div>
          </div>
        )}
      </div>

      {status === 'idle' && (
        <div 
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4 transition-all ${
            dragActive ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 hover:border-slate-400 bg-slate-50'
          }`}
        >
          <input 
            ref={fileInputRef}
            type="file" 
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleChange}
          />
          <UploadCloud className="h-12 w-12 text-slate-400" />
          <div>
            <p className="text-sm font-semibold text-slate-700">Drag and drop file here</p>
            <p className="text-xs text-slate-400 mt-1">Supports PDF, PNG, JPG, JPEG up to 10MB</p>
          </div>
          <button 
            onClick={onButtonClick}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-colors shadow cursor-pointer"
          >
            Browse Files
          </button>
        </div>
      )}

      {selectedFile && status === 'idle' && (
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-slate-200 rounded text-slate-600">
              <File className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={resetUpload}
              className="px-3 py-1.5 hover:bg-slate-200 text-slate-600 rounded text-xs font-semibold border border-slate-300 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button 
              onClick={startAnalysis}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold transition-colors shadow cursor-pointer"
            >
              Start Analysis
            </button>
          </div>
        </div>
      )}

      {status === 'processing' && (
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-emerald-700 uppercase tracking-wider">Multi-Agent Processing</span>
              <span className="text-slate-500">
                {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div 
                className="bg-emerald-600 h-full transition-all duration-500" 
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-4">
            {steps.map((step, idx) => (
              <div 
                key={step} 
                className={`flex items-center space-x-3 text-sm transition-all ${
                  idx < currentStep ? 'text-emerald-600 font-semibold' :
                  idx === currentStep ? 'text-slate-800 font-bold' :
                  'text-slate-400'
                }`}
              >
                <div className={`h-5 w-5 rounded-full flex items-center justify-center text-xs border ${
                  idx < currentStep ? 'bg-emerald-50 border-emerald-200 text-emerald-600' :
                  idx === currentStep ? 'bg-amber-50 border-amber-200 text-amber-600 animate-pulse' :
                  'bg-slate-50 border-slate-200 text-slate-400'
                }`}>
                  {idx < currentStep ? "✓" : idx + 1}
                </div>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'done' && (
        <div className="text-center py-4 space-y-6 animate-fadeIn">
          <div className="space-y-4">
            <div className="inline-flex p-3 bg-emerald-50 border border-emerald-200 rounded-full text-emerald-600">
              <CheckCircle2 className="h-10 w-10 animate-bounce" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">Invoice Successfully Analyzed!</h3>
              <p className="text-xs text-slate-500 mt-1">All five intelligence sub-agents have successfully verified transaction metrics</p>
            </div>
          </div>

          {report && (
            <div className="border border-slate-200 rounded-xl bg-slate-50 text-left overflow-hidden shadow-sm">
              <div className="flex items-center justify-between px-5 py-3 bg-slate-100 border-b border-slate-200">
                <span className="text-[10px] font-bold text-slate-700 tracking-wider uppercase font-mono">
                  VELNIX INITIAL INVESTIGATION REPORT
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCopy}
                    className="flex items-center space-x-1 px-2 py-1 hover:bg-slate-200 text-slate-600 hover:text-slate-800 rounded text-xs font-semibold border border-slate-300 transition-all bg-white shadow-sm cursor-pointer"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                  </button>
                  <button
                    onClick={handleDownload}
                    className="flex items-center space-x-1 px-2 py-1 hover:bg-slate-200 text-slate-600 hover:text-slate-800 rounded text-xs font-semibold border border-slate-300 transition-all bg-white shadow-sm cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download</span>
                  </button>
                </div>
              </div>
              <div className="p-5 font-mono text-[11px] text-slate-700 overflow-x-auto whitespace-pre leading-relaxed bg-white select-all max-h-[350px] overflow-y-auto">
                {report}
              </div>
            </div>
          )}

          <div className="flex justify-center space-x-3 border-t border-slate-100 pt-6">
            <button 
              onClick={resetUpload}
              className="px-4 py-2 hover:bg-slate-100 text-slate-700 rounded-lg text-sm font-semibold border border-slate-200 transition-colors cursor-pointer"
            >
              Analyze Another
            </button>
            <button 
              onClick={() => window.location.hash = `/invoices/${finalInvoiceId}`}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-colors shadow cursor-pointer"
            >
              View Analysis Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
