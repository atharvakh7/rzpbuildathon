import React from 'react';

interface CurrencyProps {
  amount: number | string;
  compact?: boolean;
  className?: string;
}

export const formatINR = (val: number, compact: boolean = false): string => {
  if (isNaN(val)) return '₹0';
  if (compact) {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)}L`;
    }
    if (val >= 1000) {
      return `₹${(val / 1000).toFixed(1)}k`;
    }
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);
};

export const Currency: React.FC<CurrencyProps> = ({ amount, compact = false, className = '' }) => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return <span className={`font-mono ${className}`}>{formatINR(num, compact)}</span>;
};
