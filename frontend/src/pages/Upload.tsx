import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2 } from 'lucide-react';

export const Upload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [currentStep, setCurrentStep] = useState(0);
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
      } else {
        alert("Unsupported file type. Please upload a PDF, PNG, or JPEG.");
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const startAnalysis = () => {
    if (!selectedFile) return;
    
    setStatus('processing');
    setCurrentStep(0);

    // Simulate multi-agent processing step timer ticks
    const interval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < steps.length - 1) {
          return prev + 1;
        } else {
          clearInterval(interval);
          setStatus('done');
          return prev;
        }
      });
    }, 1500);
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setStatus('idle');
    setCurrentStep(0);
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-xl border border-slate-200 shadow-sm p-8 space-y-8 animate-fadeIn">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Upload Vendor Invoice</h2>
        <p className="text-xs text-slate-500 mt-1">Submit documents for automated metadata extraction and multi-agent risk screening</p>
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
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-colors shadow"
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
              className="px-3 py-1.5 hover:bg-slate-200 text-slate-600 rounded text-xs font-semibold border border-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={startAnalysis}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold transition-colors shadow"
            >
              Start Analysis
            </button>
          </div>
        </div>
      )}

      {status === 'processing' && (
        <div className="space-y-6">
          {/* Progress bar */}
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

          {/* Stepper display */}
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
        <div className="text-center py-8 space-y-6">
          <div className="inline-flex p-3 bg-emerald-50 border border-emerald-200 rounded-full text-emerald-600">
            <CheckCircle2 className="h-10 w-10 animate-bounce" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">Invoice Successfully Analyzed!</h3>
            <p className="text-xs text-slate-500 mt-1">All five intelligence sub-agents have successfully verified transaction metrics</p>
          </div>
          <div className="flex justify-center space-x-3">
            <button 
              onClick={resetUpload}
              className="px-4 py-2 hover:bg-slate-100 text-slate-700 rounded-lg text-sm font-semibold border border-slate-200 transition-colors"
            >
              Analyze Another
            </button>
            <button 
              onClick={() => window.location.hash = "/invoices/INV-1002"}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-colors shadow"
            >
              View Analysis Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
