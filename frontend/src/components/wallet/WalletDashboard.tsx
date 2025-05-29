import React, { useEffect, useState } from 'react';
import { walletAPI } from '../../api/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { Loader2 } from 'lucide-react';

interface WalletBalance {
  balance: number;
  last_updated?: string;
}

interface Transaction {
  id: string;
  amount: number;
  timestamp: string;
  description?: string;
}

const WalletDashboard: React.FC = () => {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWalletData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const balanceData = await walletAPI.getBalance();
        setBalance(balanceData);
        
        const transactionsData = await walletAPI.getTransactions();
        setTransactions(transactionsData);
      } catch (err: any) {
        console.error('Error fetching wallet data:', err);
        setError(
          err.response?.data?.detail || 
          'Failed to load wallet data. Please try again later.'
        );
      } finally {
        setLoading(false);
      }
    };
    
    fetchWalletData();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const formatCurrency = (amount: number) => {
    return `₭ ${amount.toLocaleString()}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Wallet Balance Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Current Balance</CardDescription>
          <CardTitle className="text-4xl font-bold text-center">
            {balance ? formatCurrency(balance.balance) : '₭ 0'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {balance?.last_updated && (
            <p className="text-sm text-gray-500 text-center">
              Last updated: {formatDate(balance.last_updated)}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>
            Recent rewards and credits
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <p className="text-center text-gray-500 py-4">
              No transactions found
            </p>
          ) : (
            <div className="space-y-4">
              {transactions.map((transaction) => (
                <div key={transaction.id} className="space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">
                        {transaction.description || 'Reward'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatDate(transaction.timestamp)}
                      </p>
                    </div>
                    <p className="font-semibold text-green-600">
                      {formatCurrency(transaction.amount)}
                    </p>
                  </div>
                  <Separator />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default WalletDashboard;
