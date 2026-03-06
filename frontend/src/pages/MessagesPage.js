import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { ArrowLeft, Send, Disc, Search } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { usePageTitle } from '../hooks/usePageTitle';

const MessagesPage = () => {
  usePageTitle('Messages');
  const { user, token, API } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMsg, setNewMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [convContext, setConvContext] = useState(null);
  const [otherUser, setOtherUser] = useState(null);
  const messagesEndRef = useRef(null);
  const pollRef = useRef(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchConversations = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/dm/conversations`, { headers });
      setConversations(resp.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [API, token]);

  // Handle deep-link: ?to=userId&context=...&contextType=...&contextRecord=...
  useEffect(() => {
    const toUserId = searchParams.get('to');
    const contextType = searchParams.get('contextType');
    const contextRecord = searchParams.get('contextRecord');
    const contextAction = searchParams.get('contextAction');

    if (toUserId) {
      // Check if conversation already exists
      const checkExisting = async () => {
        try {
          const resp = await axios.get(`${API}/dm/conversation-with/${toUserId}`, { headers });
          if (resp.data.conversation_id) {
            openConversation(resp.data.conversation_id);
          } else {
            // Set up for new conversation
            const userResp = await axios.get(`${API}/users/by-id/${toUserId}`, { headers }).catch(() => null);
            setOtherUser(userResp?.data || { id: toUserId, username: '?' });
            setActiveConv('new');
            setMessages([]);
            if (contextType && contextRecord) {
              setConvContext({ type: contextType, record_name: contextRecord, action_text: contextAction || '' });
            }
          }
        } catch { /* ignore */ }
      };
      checkExisting();
      setSearchParams({}, { replace: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  // Poll for new messages in active conversation
  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (activeConv && activeConv !== 'new') {
      pollRef.current = setInterval(async () => {
        try {
          const resp = await axios.get(`${API}/dm/conversations/${activeConv}`, { headers });
          setMessages(resp.data.messages);
        } catch { /* ignore */ }
      }, 5000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [activeConv, API, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const openConversation = async (convId) => {
    setActiveConv(convId);
    try {
      const resp = await axios.get(`${API}/dm/conversations/${convId}`, { headers });
      setMessages(resp.data.messages);
      setOtherUser(resp.data.other_user);
      setConvContext(resp.data.context);
      fetchConversations(); // refresh unread counts
    } catch { /* ignore */ }
  };

  const sendMessage = async () => {
    if (!newMsg.trim()) return;
    setSending(true);
    try {
      if (activeConv === 'new') {
        // Create new conversation
        const toId = otherUser?.id || searchParams.get('to');
        const resp = await axios.post(`${API}/dm/conversations`, {
          recipient_id: toId,
          text: newMsg.trim(),
          context: convContext,
        }, { headers });
        setActiveConv(resp.data.conversation_id);
        openConversation(resp.data.conversation_id);
      } else {
        await axios.post(`${API}/dm/conversations/${activeConv}/messages`, { text: newMsg.trim() }, { headers });
        const resp = await axios.get(`${API}/dm/conversations/${activeConv}`, { headers });
        setMessages(resp.data.messages);
      }
      setNewMsg('');
      fetchConversations();
    } catch { /* ignore */ }
    finally { setSending(false); }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 pt-16 md:pt-28">
        <Skeleton className="h-8 w-40 mb-6" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full mb-3" />)}
      </div>
    );
  }

  // Thread view
  if (activeConv) {
    return (
      <div className="max-w-2xl mx-auto px-4 pt-16 md:pt-28 pb-4 flex flex-col" style={{ height: '100vh' }} data-testid="dm-thread">
        {/* Thread header */}
        <div className="flex items-center gap-3 mb-4">
          <Button variant="ghost" size="sm" onClick={() => { setActiveConv(null); setMessages([]); setConvContext(null); fetchConversations(); }} data-testid="dm-back-btn">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          {otherUser?.avatar_url ? (
            <img src={otherUser.avatar_url} alt="" className="w-9 h-9 rounded-full object-cover" />
          ) : (
            <div className="w-9 h-9 rounded-full bg-honey/30 flex items-center justify-center text-sm font-bold text-honey-amber">
              {(otherUser?.username || '?')[0].toUpperCase()}
            </div>
          )}
          <Link to={`/profile/${otherUser?.username}`} className="font-heading text-lg text-vinyl-black hover:text-honey-amber transition-colors" data-testid="dm-thread-username">
            @{otherUser?.username || '?'}
          </Link>
        </div>

        {/* Context card */}
        {convContext && (
          <Card className="p-3 mb-4 bg-purple-50 border-purple-200" data-testid="dm-context-card">
            <div className="flex items-center gap-2 text-sm text-purple-700">
              <Disc className="w-4 h-4 shrink-0" />
              <span>
                {convContext.type === 'iso' && `re: your ISO for `}
                {convContext.type === 'trade' && `re: trade listing · `}
                {convContext.type === 'listing' && `re: listing · `}
                <strong>{convContext.record_name}</strong>
                {convContext.action_text && <span className="text-purple-500 ml-1">· {convContext.action_text}</span>}
              </span>
            </div>
          </Card>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 min-h-0" data-testid="dm-messages-list">
          {messages.length === 0 && activeConv === 'new' && (
            <p className="text-center text-sm text-muted-foreground py-8">Start the conversation...</p>
          )}
          {messages.map(msg => {
            const isMine = msg.sender_id === user?.id;
            return (
              <div key={msg.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`} data-testid={`dm-msg-${msg.id}`}>
                <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm ${isMine ? 'bg-honey text-vinyl-black rounded-br-md' : 'bg-white border border-honey/30 text-vinyl-black rounded-bl-md'}`}>
                  <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                  <p className={`text-[10px] mt-1 ${isMine ? 'text-vinyl-black/50' : 'text-muted-foreground'}`}>
                    {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex gap-2" data-testid="dm-input-area">
          <Input
            value={newMsg} onChange={e => setNewMsg(e.target.value)} onKeyDown={handleKeyDown}
            placeholder="Type a message..." className="flex-1 border-honey/50 rounded-full px-4"
            data-testid="dm-input" autoFocus
          />
          <Button onClick={sendMessage} disabled={sending || !newMsg.trim()}
            className="bg-honey text-vinyl-black hover:bg-honey-amber rounded-full h-10 w-10 p-0 shrink-0" data-testid="dm-send-btn">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    );
  }

  // Conversation list
  return (
    <div className="max-w-2xl mx-auto px-4 py-8 pt-16 md:pt-28 pb-24 md:pb-8" data-testid="dm-inbox">
      <h1 className="font-heading text-3xl text-vinyl-black mb-6">Messages</h1>

      {conversations.length === 0 ? (
        <Card className="p-8 text-center border-honey/30">
          <Search className="w-12 h-12 text-honey/40 mx-auto mb-4" />
          <h3 className="font-heading text-xl mb-2">No messages yet</h3>
          <p className="text-muted-foreground text-sm">Start a conversation from someone's profile or a Wantlist card.</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {conversations.map(conv => (
            <button key={conv.id} onClick={() => openConversation(conv.id)}
              className="w-full text-left p-4 rounded-xl bg-white border border-honey/20 hover:border-honey/50 hover:shadow-sm transition-all flex items-center gap-3"
              data-testid={`dm-conv-${conv.id}`}>
              {conv.other_user?.avatar_url ? (
                <img src={conv.other_user.avatar_url} alt="" className="w-11 h-11 rounded-full object-cover shrink-0" />
              ) : (
                <div className="w-11 h-11 rounded-full bg-honey/30 flex items-center justify-center text-base font-bold text-honey-amber shrink-0">
                  {(conv.other_user?.username || '?')[0].toUpperCase()}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`font-medium text-sm ${conv.unread_count > 0 ? 'text-vinyl-black' : 'text-vinyl-black/80'}`}>
                    @{conv.other_user?.username || '?'}
                  </span>
                  <span className="text-[11px] text-muted-foreground shrink-0">
                    {conv.last_message_at && formatDistanceToNow(new Date(conv.last_message_at), { addSuffix: true })}
                  </span>
                </div>
                <p className={`text-sm truncate mt-0.5 ${conv.unread_count > 0 ? 'text-vinyl-black font-medium' : 'text-muted-foreground'}`}>
                  {conv.last_message || 'No messages yet'}
                </p>
              </div>
              {conv.unread_count > 0 && (
                <span className="bg-honey text-vinyl-black text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shrink-0" data-testid={`dm-unread-${conv.id}`}>
                  {conv.unread_count}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default MessagesPage;
