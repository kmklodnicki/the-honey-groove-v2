import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Heart, MessageCircle, MoreVertical, Trash2, Pin, Reply, Send, ChevronDown, ChevronUp, Sparkles, X, FileText, Camera, Loader2, Share2 } from 'lucide-react';
import { useShareCard } from '../hooks/useShareCard';
import NowSpinningCard from './ShareCards/NowSpinningCard';
import NewHaulCard from './ShareCards/NewHaulCard';
import SaleCard from './ShareCards/SaleCard';
import DailyPromptShareCard from './ShareCards/DailyPromptCard';
import ISOShareCard from './ShareCards/ISOCard';
import UserBadges from './UserBadges';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from './ui/dropdown-menu';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from './ui/alert-dialog';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { resolveImageUrl } from '../utils/imageUrl';
import { PostTypeBadge, PostCardBody, NewFeatureBadge, FormatPill } from './PostCards';
import { TitleBadge } from './TitleBadge';
import CommentThread from './CommentItem';
import LoadingHoney from './LoadingHoney';
import { validateImageFile, prepareImageForUpload } from '../utils/imageUpload';

export const InfiniteScrollSentinel = ({ onIntersect, loading }) => {
  const sentinelRef = useRef(null);
  const callbackRef = useRef(onIntersect);
  callbackRef.current = onIntersect;

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !loading) callbackRef.current(); },
      { rootMargin: '400px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loading]);
  return (
    <div ref={sentinelRef} className="flex justify-center py-4" data-testid="infinite-scroll-sentinel">
      {loading && <LoadingHoney size="sm" text="" className="py-2" />}
    </div>
  );
};

export const BeeAvatar = ({ user, className = "h-10 w-10" }) => {
  const firstLetter = user?.username?.charAt(0).toUpperCase() || '?';
  const hasCustomAvatar = user?.avatar_url && !user.avatar_url.includes('dicebear');
  return (
    <Avatar className={`${className} border-2 border-honey/30`}>
      {hasCustomAvatar && <AvatarImage src={resolveImageUrl(user.avatar_url)} alt={user?.username} />}
      <AvatarFallback className="bg-honey-soft text-vinyl-black relative">
        <span className="font-heading">{firstLetter}</span>
        <svg viewBox="0 0 24 24" className="absolute -bottom-0.5 -right-0.5 w-3 h-3" fill="none">
          <ellipse cx="12" cy="14" rx="5" ry="4" fill="#1E2A3A"/>
          <ellipse cx="12" cy="13" rx="3.5" ry="2" fill="#D4A828"/>
          <circle cx="12" cy="9" r="2.5" fill="#1E2A3A"/>
        </svg>
      </AvatarFallback>
    </Avatar>
  );
};

export const PostCard = ({ post, onLike, onCommentCountChange, onDelete, onAlbumClick, onPin, onToggleFeature, onToggleReleaseNote, token, API, currentUserId, isAdmin, highlighted, autoOpenComments, imgPriority, obscureIdentity }) => {
  const [showComments, setShowComments] = useState(!!autoOpenComments);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [commentToDelete, setCommentToDelete] = useState(null);
  const [replyTo, setReplyTo] = useState(null);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionResults, setMentionResults] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const commentInputRef = React.useRef(null);
  const mentionTimerRef = React.useRef(null);
  const cardRef = useRef(null);
  const commentPhotoRef = React.useRef(null);
  const [commentPhoto, setCommentPhoto] = useState(null);
  const [commentPhotoPreview, setCommentPhotoPreview] = useState(null);
  const [photoUploading, setPhotoUploading] = useState(false);

  // Collapsible pinned post — persisted in localStorage
  const pinnedKey = post.is_pinned ? `hg_pin_collapsed_${post.id}` : null;
  const [pinnedCollapsed, setPinnedCollapsed] = useState(() => {
    if (!post.is_pinned) return false;
    try { return localStorage.getItem(`hg_pin_collapsed_${post.id}`) === '1'; } catch { return false; }
  });
  const togglePinnedCollapse = () => {
    const next = !pinnedCollapsed;
    setPinnedCollapsed(next);
    try { if (next) localStorage.setItem(pinnedKey, '1'); else localStorage.removeItem(pinnedKey); } catch {}
  };

  // Collapsible release note — persisted in localStorage
  const releaseNoteKey = post.is_release_note ? `hg_rn_collapsed_${post.id}` : null;
  const [rnCollapsed, setRnCollapsed] = useState(() => {
    if (!post.is_release_note) return false;
    try { return localStorage.getItem(`hg_rn_collapsed_${post.id}`) === '1'; } catch { return false; }
  });
  const toggleRnCollapse = () => {
    const next = !rnCollapsed;
    setRnCollapsed(next);
    try { if (next) localStorage.setItem(releaseNoteKey, '1'); else localStorage.removeItem(releaseNoteKey); } catch {}
  };

  const isOwner = post.user_id === currentUserId;
  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true });

  // Share card — for spins, hauls, and sale listings
  const isShareable = ['NOW_SPINNING', 'NEW_HAUL', 'listing_sale', 'DAILY_PROMPT'].includes(post.post_type);
  const cardTypeMap = { NEW_HAUL: 'haul', listing_sale: 'sale', DAILY_PROMPT: 'daily_prompt' };
  const filenameMap = { NEW_HAUL: 'haul', listing_sale: 'sale', DAILY_PROMPT: 'daily-prompt' };
  const { cardRef: shareCardRef, exporting: shareExporting, exportCard } = useShareCard({
    cardType: cardTypeMap[post.post_type] || 'now_spinning',
    filename: `thg-${filenameMap[post.post_type] || 'now-spinning'}`,
    title: `${post.user?.username ? `@${post.user.username} on ` : ''}The Honey Groove`,
    userId: currentUserId,
  });
  const handleSharePost = () => {
    const coverUrl = post.cover_url || post.record?.cover_url || post.bundle_records?.[0]?.cover_url;
    exportCard([coverUrl].filter(Boolean));
  };

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const response = await axios.get(`${API}/posts/${post.id}/comments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleToggleComments = () => {
    if (!showComments && comments.length === 0) fetchComments();
    setShowComments(!showComments);
  };

  useEffect(() => {
    if (highlighted && cardRef.current) {
      setTimeout(() => {
        const y = cardRef.current.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }, 300);
    }
    if (autoOpenComments && comments.length === 0) {
      fetchComments();
    }
  }, [highlighted, autoOpenComments]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCommentPhotoSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const err = validateImageFile(file);
    if (err) { toast.error(err); e.target.value = ''; return; }
    const prepared = await prepareImageForUpload(file);
    setCommentPhoto(prepared);
    setCommentPhotoPreview(URL.createObjectURL(prepared));
  };

  const clearCommentPhoto = () => {
    setCommentPhoto(null);
    setCommentPhotoPreview(null);
    if (commentPhotoRef.current) commentPhotoRef.current.value = '';
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() && !commentPhoto) return;
    setSubmitting(true);
    const content = newComment.trim() || ' ';
    const parentId = replyTo?.id || null;

    // Upload photo first if present
    let imageUrl = null;
    if (commentPhoto) {
      setPhotoUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', commentPhoto);
        const uploadRes = await axios.post(`${API}/upload`, formData, {
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
        });
        imageUrl = uploadRes.data.url;
      } catch (err) {
        toast.error(err.response?.data?.detail || 'image upload failed. try a different photo.');
        setSubmitting(false);
        setPhotoUploading(false);
        return;
      }
      setPhotoUploading(false);
    }

    const optimisticId = `opt_${Date.now()}`;
    const optimisticComment = {
      id: optimisticId, post_id: post.id, user_id: currentUserId, content, parent_id: parentId,
      created_at: new Date().toISOString(), user: { id: currentUserId, username: 'you' },
      likes_count: 0, is_liked: false, replies: [], _optimistic: true,
      image_url: imageUrl,
    };
    if (parentId) {
      setComments(prev => prev.map(c => c.id === parentId ? { ...c, replies: [...(c.replies || []), optimisticComment] } : c));
    } else {
      setComments(prev => [...prev, optimisticComment]);
    }
    setNewComment(''); setReplyTo(null); setShowMentions(false);
    clearCommentPhoto();
    onCommentCountChange(post.id, 1);
    try {
      const response = await axios.post(`${API}/posts/${post.id}/comments`,
        { post_id: post.id, content, parent_id: parentId, image_url: imageUrl },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      if (parentId) {
        setComments(prev => prev.map(c => c.id === parentId ? { ...c, replies: (c.replies || []).map(r => r.id === optimisticId ? { ...response.data, replies: [] } : r) } : c));
      } else {
        setComments(prev => prev.map(c => c.id === optimisticId ? { ...response.data, replies: [] } : c));
      }
    } catch {
      if (parentId) {
        setComments(prev => prev.map(c => c.id === parentId ? { ...c, replies: (c.replies || []).filter(r => r.id !== optimisticId) } : c));
      } else {
        setComments(prev => prev.filter(c => c.id !== optimisticId));
      }
      onCommentCountChange(post.id, -1);
      toast.error('something went wrong. please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = (comment) => {
    const parentId = comment._replyParentId || comment.id;
    setReplyTo({ id: parentId, username: comment.user?.username });
    setNewComment(`@${comment.user?.username} `);
    setTimeout(() => { if (commentInputRef.current) { commentInputRef.current.focus(); commentInputRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' }); } }, 50);
  };

  const handleCommentLike = async (commentId, isLiked) => {
    const updateLike = (list) => list.map(c => {
      if (c.id === commentId) return { ...c, is_liked: !isLiked, likes_count: isLiked ? Math.max(0, c.likes_count - 1) : c.likes_count + 1 };
      if (c.replies?.length) return { ...c, replies: updateLike(c.replies) };
      return c;
    });
    setComments(prev => updateLike(prev));
    try {
      if (isLiked) {
        await axios.delete(`${API}/comments/${commentId}/like`, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await axios.post(`${API}/comments/${commentId}/like`, {}, { headers: { Authorization: `Bearer ${token}` } });
      }
    } catch {
      const revertLike = (list) => list.map(c => {
        if (c.id === commentId) return { ...c, is_liked: isLiked, likes_count: isLiked ? c.likes_count + 1 : Math.max(0, c.likes_count - 1) };
        if (c.replies?.length) return { ...c, replies: revertLike(c.replies) };
        return c;
      });
      setComments(prev => revertLike(prev));
    }
  };

  const handleDeleteComment = (comment) => setCommentToDelete(comment);

  const confirmDeleteComment = async () => {
    if (!commentToDelete) return;
    const cid = commentToDelete.id;
    const markDeleted = (list) => list.map(c => {
      if (c.id === cid) return { ...c, is_deleted: true, content: '[deleted]' };
      if (c.replies?.length) return { ...c, replies: markDeleted(c.replies) };
      return c;
    }).filter(c => !c.is_deleted || (c.replies?.length > 0));
    setComments(prev => markDeleted(prev));
    setCommentToDelete(null);
    if (onCommentCountChange) onCommentCountChange(post.id, -1);
    try {
      await axios.delete(`${API}/comments/${cid}`, { headers: { Authorization: `Bearer ${token}` } });
    } catch {
      fetchComments();
    }
  };

  const handleCommentInputChange = (e) => {
    const val = e.target.value;
    setNewComment(val);
    const cursorPos = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursorPos);
    const atMatch = textBeforeCursor.match(/@(\w*)$/);
    if (atMatch && atMatch[1].length >= 1) {
      const query = atMatch[1];
      setMentionQuery(query);
      if (mentionTimerRef.current) clearTimeout(mentionTimerRef.current);
      mentionTimerRef.current = setTimeout(async () => {
        try {
          const res = await axios.get(`${API}/mention-search`, { params: { q: query }, headers: { Authorization: `Bearer ${token}` } });
          setMentionResults(res.data);
          setShowMentions(res.data.length > 0);
        } catch { setShowMentions(false); }
      }, 200);
    } else {
      setShowMentions(false);
    }
  };

  const insertMention = (username) => {
    const cursorPos = commentInputRef.current?.selectionStart || newComment.length;
    const textBeforeCursor = newComment.slice(0, cursorPos);
    const textAfterCursor = newComment.slice(cursorPos);
    const replaced = textBeforeCursor.replace(/@(\w*)$/, `@${username} `);
    setNewComment(replaced + textAfterCursor);
    setShowMentions(false);
    setTimeout(() => commentInputRef.current?.focus(), 50);
  };

  // Post type banner config — label + icon for each type
  const POST_TYPE_BANNER = {
    NOW_SPINNING:        { label: 'Now Spinning',        icon: '🎵' },
    RANDOMIZER:          { label: 'Now Spinning',        icon: '🎵' },
    NEW_HAUL:            { label: 'Haul',                icon: '📦' },
    ISO:                 { label: 'ISO',                 icon: '🔍' },
    NOTE:                { label: 'Note',                icon: '📝' },
    DAILY_PROMPT:        { label: 'Daily Prompt',        icon: '🐝' },
    POLL:                { label: 'Poll',                icon: '📊' },
    listing_sale:        { label: 'For Sale',            icon: '🏷️' },
    listing_trade:       { label: 'For Trade',           icon: '🔄' },
    WEEKLY_WRAP:         { label: 'Weekly Wrap',         icon: '🎶' },
    VINYL_MOOD:          { label: 'Vinyl Mood',          icon: '🌙' },
    ADDED_TO_COLLECTION: { label: 'Added to Collection', icon: '➕' },
    ROOM_JOIN:           { label: 'Joined a Room',       icon: '🍯' },
    RELEASE_NOTE:        { label: 'Release Note',        icon: '✏️' },
  };
  const bannerConfig = POST_TYPE_BANNER[post.post_type] || POST_TYPE_BANNER.NOW_SPINNING;
  const spinCount = post.user?.spin_count ?? 0;

  return (
    <Card ref={cardRef} className={`overflow-hidden transition-all ${highlighted ? 'ring-2 ring-honey shadow-lg shadow-honey/20' : ''} ${post.is_new_feature ? 'shadow-md' : ''}`} style={{ background: 'rgba(255,255,255,0.65)', backdropFilter: 'blur(6px)', border: post.is_new_feature ? '1px solid rgba(212,168,40,0.18)' : '1px solid rgba(212,168,40,0.08)', borderRadius: '12px', ...(post.is_new_feature ? { backgroundColor: 'rgba(243,250,245,0.8)' } : {}) }} data-testid={`post-${post.id}`}>
      {/* Post Type Banner */}
      {!post.is_release_note && !post.is_pinned && (
        <div
          style={{ background: '#354B66', padding: '5px 16px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '12px 12px 0 0' }}
          data-testid={`post-type-banner-${post.id}`}
        >
          <span style={{ fontSize: '10px' }}>{bannerConfig.icon}</span>
          <span style={{ fontSize: '9px', fontWeight: 700, color: '#E8CA5A', textTransform: 'uppercase', letterSpacing: '1px' }}>{bannerConfig.label}</span>
          {spinCount > 0 && <span style={{ fontSize: '9px', color: '#F0E6C8', marginLeft: 'auto' }}>🎵 {spinCount} spins</span>}
        </div>
      )}
      {post.is_pinned && (
        <div style={{ background: '#354B66', padding: '5px 16px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '12px 12px 0 0', color: '#E8CA5A' }} data-testid={`pinned-${post.id}`}>
          <Pin className="w-3 h-3" style={{ color: '#E8CA5A' }} />
          <span style={{ fontSize: '9px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', flex: 1 }}>{pinnedCollapsed ? 'Pinned Post' : 'Pinned'}</span>
          <button
            onClick={(e) => { e.stopPropagation(); togglePinnedCollapse(); }}
            className="p-0.5 rounded transition-colors"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#E8CA5A' }}
            data-testid={`pinned-toggle-${post.id}`}
            aria-label={pinnedCollapsed ? 'Expand pinned post' : 'Collapse pinned post'}
          >
            {pinnedCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}
      {post.is_release_note && !post.is_pinned && (
        <div style={{ background: '#354B66', padding: '5px 16px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '12px 12px 0 0', color: '#E8CA5A' }} data-testid={`release-note-banner-${post.id}`}>
          <FileText className="w-3 h-3" style={{ color: '#E8CA5A' }} />
          <span style={{ fontSize: '9px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', flex: 1 }}>Release Note</span>
          <button
            onClick={(e) => { e.stopPropagation(); toggleRnCollapse(); }}
            className="p-0.5 rounded transition-colors"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#E8CA5A' }}
            data-testid={`release-note-toggle-${post.id}`}
            aria-label={rnCollapsed ? 'Expand release note' : 'Collapse release note'}
          >
            {rnCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}
      {/* If pinned/release-note and collapsed, hide the rest of the card */}
      {!(post.is_pinned && pinnedCollapsed) && !(post.is_release_note && rnCollapsed) && (<>
      <div className="p-4 pb-2">
        <div className="flex items-center gap-3">
          {obscureIdentity ? (
            <div className="select-none pointer-events-none" aria-hidden="true">
              <BeeAvatar user={null} className="h-10 w-10 blur-sm opacity-60" />
            </div>
          ) : (
            <Link to={`/profile/${post.user?.username}`}>
              <BeeAvatar user={post.user} />
            </Link>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {obscureIdentity ? (
                <span
                  className="font-medium select-none blur-sm opacity-60 pointer-events-none"
                  aria-hidden="true"
                >
                  @{post.user?.username || 'member'}
                </span>
              ) : (
                <Link to={`/profile/${post.user?.username}`} className="font-medium hover:underline">
                  @{post.user?.username}
                </Link>
              )}
              <UserBadges user={post.user} size="small" />
              {post.user?.title_label && <TitleBadge label={post.user.title_label} />}
              <PostTypeBadge type={post.post_type} mood={post.mood} isReleaseNote={post.is_release_note} />
              {post.record_id && <FormatPill format={post.record_format || post.record?.format || 'Vinyl'} />}
              {!post.record_id && post.bundle_records?.length > 0 && <FormatPill format={post.bundle_records[0]?.format || 'Vinyl'} />}
              {post.is_new_feature && <NewFeatureBadge />}
            </div>
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>
          {(isOwner || isAdmin) && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="p-1.5 rounded-full hover:bg-honey/10 transition-colors" data-testid={`post-menu-${post.id}`}>
                  <MoreVertical className="w-4 h-4 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {isOwner && (
                  <DropdownMenuItem onClick={() => setDeleteDialogOpen(true)} className="text-red-600" data-testid={`delete-post-${post.id}`}>
                    <Trash2 className="mr-2 h-4 w-4" /> Delete Post
                  </DropdownMenuItem>
                )}
                {isAdmin && (
                  <DropdownMenuItem onClick={() => onPin(post.id, post.is_pinned)} data-testid={`pin-post-${post.id}`}>
                    <Pin className="mr-2 h-4 w-4" /> {post.is_pinned ? 'Unpin Post' : 'Pin to Top'}
                  </DropdownMenuItem>
                )}
                {isAdmin && (
                  <DropdownMenuItem onClick={() => onToggleFeature(post.id, post.is_new_feature)} data-testid={`toggle-feature-${post.id}`}>
                    <Sparkles className="mr-2 h-4 w-4" /> {post.is_new_feature ? 'Remove New Feature' : 'Tag as New Feature'}
                  </DropdownMenuItem>
                )}
                {isAdmin && (
                  <DropdownMenuItem onClick={() => onToggleReleaseNote(post.id, post.is_release_note)} data-testid={`toggle-release-note-${post.id}`}>
                    <FileText className="mr-2 h-4 w-4" /> {post.is_release_note ? 'Remove Release Note' : 'Convert to Release Note'}
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
      <div className="px-4 py-2">
        <PostCardBody post={post} onAlbumClick={onAlbumClick} imgPriority={imgPriority} />
      </div>
      <div className="px-4 py-3 flex items-center gap-4 border-t border-honey/20">
        <button type="button" onClick={(e) => { e.stopPropagation(); onLike(post.id, post.is_liked); }}
          className={`flex items-center gap-1.5 text-sm transition-all p-2 -m-2 rounded-full ${post.is_liked ? 'text-[#D4A828] honey-like-burst' : 'text-muted-foreground hover:text-[#D4A828]'}`}
          style={{ touchAction: 'manipulation' }} data-testid={`like-btn-${post.id}`}>
          <Heart className={`w-4 h-4 transition-all duration-200 ${post.is_liked ? 'fill-current scale-110 honey-like-pop' : 'hover:scale-110'}`} />
          {post.likes_count > 0 && <span className={post.is_liked ? 'count-bump' : ''}>{post.likes_count}</span>}
        </button>
        <button onClick={handleToggleComments}
          className={`flex items-center gap-1.5 text-sm transition-colors ${showComments ? 'text-honey-amber' : 'text-muted-foreground hover:text-honey-amber'}`}
          data-testid={`comment-btn-${post.id}`}>
          <MessageCircle className={`w-4 h-4 ${showComments ? 'fill-honey/30' : ''}`} />
          {post.comments_count > 0 && post.comments_count}
          {showComments ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
        {isShareable && (
          <button
            onClick={handleSharePost}
            disabled={shareExporting}
            className="ml-auto flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full transition-opacity disabled:opacity-50 hover:opacity-80"
            style={{ background: '#1E2A3A', color: '#E8CA5A' }}
            title="Share to Stories"
            data-testid={`share-btn-${post.id}`}
          >
            {shareExporting
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <Share2 className="w-3.5 h-3.5" />
            }
            <span>Share</span>
          </button>
        )}
      </div>

      {/* Hidden share card — rendered off-screen for html2canvas capture */}
      {isShareable && post.post_type === 'DAILY_PROMPT' ? (
        <DailyPromptShareCard
          ref={shareCardRef}
          promptQuestion={post.prompt_text}
          record={{
            cover_url: post.cover_url,
            title: post.record_title,
            artist: post.record_artist,
          }}
          user={post.user}
        />
      ) : isShareable && post.post_type === 'listing_sale' ? (
        <SaleCard
          ref={shareCardRef}
          record={{
            cover_url: post.cover_url || post.record?.cover_url,
            title: post.record_title || post.record?.title,
            artist: post.record_artist || post.record?.artist,
          }}
          price={post.price || post.listing_price}
          user={post.user}
        />
      ) : isShareable && post.post_type === 'NEW_HAUL' ? (
        <NewHaulCard
          ref={shareCardRef}
          post={{
            cover_url: post.cover_url || post.record?.cover_url || post.bundle_records?.[0]?.cover_url,
            title: post.record_title || post.record?.title || post.bundle_records?.[0]?.title || post.caption,
            artist: post.record_artist || post.record?.artist || post.bundle_records?.[0]?.artist,
            color_variant: post.color_variant || post.record?.color_variant,
            bundle_records: post.bundle_records,
          }}
          user={post.user}
        />
      ) : isShareable && (post.post_type === 'iso' || post.post_type === 'ISO') ? (
        <ISOShareCard
          ref={shareCardRef}
          record={{
            cover_url: post.cover_url || post.record?.cover_url,
            title: post.record_title || post.record?.title || post.caption,
            artist: post.record_artist || post.record?.artist,
          }}
          user={post.user}
        />
      ) : isShareable ? (
        <NowSpinningCard
          ref={shareCardRef}
          post={{
            cover_url: post.cover_url || post.record?.cover_url,
            title: post.record_title || post.record?.title || post.caption,
            artist: post.record_artist || post.record?.artist,
            color_variant: post.color_variant || post.record?.color_variant,
          }}
          user={post.user}
        />
      ) : null}
      {showComments && (
        <div className="px-4 pb-4 border-t border-honey/20 bg-honey/5">
          {loadingComments ? (
            <LoadingHoney size="sm" />
          ) : (
            <>
              <div className="py-3 space-y-3 max-h-80 overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground py-2">No comments yet. Be the first!</p>
                ) : (
                  comments.map(comment => (
                    <CommentThread key={comment.id} comment={comment} onReply={handleReply} onLike={handleCommentLike} onDelete={handleDeleteComment} currentUserId={currentUserId} isAdmin={isAdmin} />
                  ))
                )}
              </div>
              {replyTo && (
                <div className="flex items-center gap-2 pt-2 text-xs text-honey-amber">
                  <Reply className="w-3 h-3" />
                  <span>replying to @{replyTo.username}</span>
                  <button onClick={() => { setReplyTo(null); setNewComment(''); }} className="ml-auto text-muted-foreground hover:text-red-500">cancel</button>
                </div>
              )}
              <div className="relative">
                {showMentions && (
                  <div className="absolute bottom-full left-0 right-0 bg-white border border-honey/30 rounded-lg shadow-lg z-10 max-h-40 overflow-y-auto mb-1" data-testid="mention-dropdown">
                    {mentionResults.map(u => (
                      <button key={u.id} onClick={() => insertMention(u.username)} className="w-full flex items-center gap-2 px-3 py-2 hover:bg-honey/10 text-sm text-left" data-testid={`mention-${u.username}`}>
                        <BeeAvatar user={u} className="h-6 w-6" />
                        <span>@{u.username}</span>
                      </button>
                    ))}
                  </div>
                )}
                <form onSubmit={handleSubmitComment} className="pt-2 border-t border-honey/20">
                  {commentPhotoPreview && (
                    <div className="mb-2 relative inline-block" data-testid={`comment-photo-preview-${post.id}`}>
                      <img src={commentPhotoPreview} alt="Attachment" className="h-16 w-16 object-cover rounded-lg border border-[#E5DBC8]" />
                      <button type="button" onClick={clearCommentPhoto} className="absolute -top-1.5 -right-1.5 bg-black/70 text-white rounded-full p-0.5" data-testid={`comment-photo-remove-${post.id}`}>
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  <div className="flex gap-2 items-center">
                    <input type="file" ref={commentPhotoRef} className="hidden" accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.jpg,.jpeg,.png,.webp,.heic,.heif" onChange={handleCommentPhotoSelect} data-testid={`comment-photo-input-${post.id}`} />
                    <button type="button" onClick={() => commentPhotoRef.current?.click()} className="shrink-0 p-1.5 rounded-full text-[#7A8694] hover:text-honey-amber hover:bg-honey/10 transition-colors" data-testid={`comment-camera-btn-${post.id}`} disabled={photoUploading}>
                      {photoUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
                    </button>
                    <Input ref={commentInputRef} placeholder={replyTo ? `Reply to @${replyTo.username}...` : "Write a comment..."}
                      value={newComment} onChange={handleCommentInputChange}
                      onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault(); }}
                      className="flex-1 h-9 text-sm border-honey/50" data-testid={`comment-input-${post.id}`} />
                    <Button type="submit" size="sm" disabled={submitting || photoUploading || (!newComment.trim() && !commentPhoto)}
                      className="bg-honey text-vinyl-black hover:bg-honey-amber h-9 px-3" data-testid={`comment-submit-${post.id}`}>
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </form>
              </div>
            </>
          )}
        </div>
      )}
      </>)}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Are you sure you want to delete this post?</AlertDialogTitle>
            <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid={`cancel-delete-${post.id}`}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => onDelete(post.id)} className="bg-red-600 text-white hover:bg-red-700" data-testid={`confirm-delete-${post.id}`}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog open={!!commentToDelete} onOpenChange={(open) => !open && setCommentToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Delete Comment?</AlertDialogTitle>
            <AlertDialogDescription>Are you sure you want to remove this? This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-comment">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteComment} className="bg-red-600 text-white hover:bg-red-700" data-testid="confirm-delete-comment">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
};
