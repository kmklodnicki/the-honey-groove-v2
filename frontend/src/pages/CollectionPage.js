import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Disc, Plus, Search, Play, Trash2, MoreVertical } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';

const CollectionPage = () => {
  const { user, token, API } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [spinDialogOpen, setSpinDialogOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [spinningRecordId, setSpinningRecordId] = useState(null);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      const response = await axios.get(`${API}/records`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecords(response.data);
    } catch (error) {
      console.error('Failed to fetch records:', error);
      toast.error('Failed to load collection');
    } finally {
      setLoading(false);
    }
  };

  const handleLogSpin = async (record) => {
    setSpinningRecordId(record.id);
    try {
      await axios.post(`${API}/spins`, 
        { record_id: record.id },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      toast.success(`Now spinning: ${record.title}`);
      fetchRecords(); // Refresh to update spin count
    } catch (error) {
      console.error('Failed to log spin:', error);
      toast.error('Failed to log spin');
    } finally {
      setSpinningRecordId(null);
    }
  };

  const handleDeleteRecord = async (recordId) => {
    if (!confirm('Are you sure you want to remove this record from your collection?')) return;

    try {
      await axios.delete(`${API}/records/${recordId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecords(records.filter(r => r.id !== recordId));
      toast.success('Record removed from collection');
    } catch (error) {
      console.error('Failed to delete record:', error);
      toast.error('Failed to remove record');
    }
  };

  const filteredRecords = records.filter(record => 
    record.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    record.artist.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 pt-24">
        <h1 className="font-heading text-3xl mb-6">My Collection</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i} className="aspect-square">
              <Skeleton className="w-full h-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 pt-24 pb-24 md:pb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading text-3xl text-vinyl-black">My Collection</h1>
          <p className="text-muted-foreground">{records.length} records</p>
        </div>
        <div className="flex gap-3">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search collection..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 border-honey/50"
              data-testid="collection-search"
            />
          </div>
          <Link to="/add-record">
            <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2" data-testid="add-record-btn">
              <Plus className="w-4 h-4" />
              Add
            </Button>
          </Link>
        </div>
      </div>

      {records.length === 0 ? (
        <Card className="p-12 text-center border-honey/30">
          <div className="w-20 h-20 bg-honey/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Disc className="w-10 h-10 text-honey-amber" />
          </div>
          <h3 className="font-heading text-2xl mb-2">Your collection is empty</h3>
          <p className="text-muted-foreground mb-6">Start building your vinyl collection today!</p>
          <Link to="/add-record">
            <Button className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full gap-2">
              <Plus className="w-4 h-4" />
              Add Your First Record
            </Button>
          </Link>
        </Card>
      ) : filteredRecords.length === 0 ? (
        <Card className="p-8 text-center border-honey/30">
          <p className="text-muted-foreground">No records match your search</p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredRecords.map(record => (
            <RecordCard 
              key={record.id} 
              record={record}
              onSpin={handleLogSpin}
              onDelete={handleDeleteRecord}
              isSpinning={spinningRecordId === record.id}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const RecordCard = ({ record, onSpin, onDelete, isSpinning }) => {
  return (
    <Card 
      className="group border-honey/30 overflow-hidden hover:shadow-honey transition-all hover:-translate-y-1"
      data-testid={`record-card-${record.id}`}
    >
      <Link to={`/record/${record.id}`}>
        <div className="relative aspect-square bg-vinyl-black">
          {record.cover_url ? (
            <img 
              src={record.cover_url} 
              alt={record.title}
              className={`w-full h-full object-cover ${isSpinning ? 'animate-spin-slow' : ''}`}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Disc className={`w-16 h-16 text-honey ${isSpinning ? 'animate-spin-slow' : ''}`} />
            </div>
          )}
          
          {/* Spin count badge */}
          {record.spin_count > 0 && (
            <div className="absolute bottom-2 left-2 bg-honey text-vinyl-black text-xs px-2 py-1 rounded-full font-medium">
              {record.spin_count} {record.spin_count === 1 ? 'spin' : 'spins'}
            </div>
          )}
        </div>
      </Link>

      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <Link to={`/record/${record.id}`} className="flex-1 min-w-0">
            <h4 className="font-medium text-sm truncate hover:text-honey-amber transition-colors">
              {record.title}
            </h4>
            <p className="text-xs text-muted-foreground truncate">{record.artist}</p>
          </Link>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSpin(record)} data-testid={`spin-btn-${record.id}`}>
                <Play className="w-4 h-4 mr-2" />
                Log Spin
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => onDelete(record.id)} 
                className="text-red-600"
                data-testid={`delete-btn-${record.id}`}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Remove
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Quick spin button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.preventDefault();
            onSpin(record);
          }}
          disabled={isSpinning}
          className="w-full mt-2 h-8 text-xs gap-1 bg-honey/10 hover:bg-honey/30"
        >
          <Play className="w-3 h-3" />
          {isSpinning ? 'Spinning...' : 'Spin Now'}
        </Button>
      </div>
    </Card>
  );
};

export default CollectionPage;
