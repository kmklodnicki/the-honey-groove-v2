import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Reply, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import BeeAvatar from './BeeAvatar';
import { TitleBadge } from './TitleBadge';

const renderMentions = (text) => {
  const parts = text.split(/(@\w+)/g);
  return parts.map((part, i) => {
    if (part.startsWith('@')) {
      const username = part.slice(1);
      return <Link key={i} to={`/profile/${username}`} className="text-honey-amber font-medium hover:underline">{part}</Link>;
    }
    return part;
  });
};

const SingleComment = ({ comment, onReply, onLike, onDelete, isReply, topLevelId, currentUserId, isAdmin }) => {
  const isDeleted = comment.is_deleted;
  const canDelete = !isDeleted && (comment.user_id === currentUserId || isAdmin);

  if (isDeleted) {
    return (
      <div className={isReply ? 'ml-8 pl-3 relative' : ''} data-testid={`comment-${comment.id}`}>
        {isReply && (
          <div className="absolute left-0 top-0 bottom-0" style={{ width: '2px', background: 'rgba(218, 165, 32, 0.2)', borderRadius: '1px' }} data-testid={`thread-line-${comment.id}`} />
        )}
        <div className="flex gap-2 py-1.5">
          <div className={`${isReply ? 'h-6 w-6' : 'h-8 w-8'} rounded-full bg-stone-200 shrink-0`} />
          <p className="text-sm italic text-muted-foreground" data-testid={`deleted-comment-${comment.id}`}>This comment has been deleted</p>
        </div>
      </div>
    );
  }

  return (
    <div className={isReply ? 'ml-8 pl-3 relative' : ''} data-testid={`comment-${comment.id}`}>
      {isReply && (
        <div className="absolute left-0 top-0 bottom-0" style={{ width: '2px', background: 'rgba(218, 165, 32, 0.2)', borderRadius: '1px' }} data-testid={`thread-line-${comment.id}`} />
      )}
      <div className="flex gap-2">
        <Link to={`/profile/${comment.user?.username}`}>
          <BeeAvatar user={comment.user} className={isReply ? 'h-6 w-6' : 'h-8 w-8'} />
        </Link>
        <div className="flex-1 bg-white rounded-lg px-3 py-2">
          <div className="flex items-center gap-2">
            <Link to={`/profile/${comment.user?.username}`} className="font-medium text-sm hover:underline">
              @{comment.user?.username}
            </Link>
            {comment.user?.title_label && <TitleBadge label={comment.user.title_label} />}
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
            </span>
            {canDelete && (
              <button
                onClick={() => onDelete(comment)}
                className="ml-auto p-1 rounded-full text-muted-foreground hover:text-red-500 hover:bg-red-50 transition-colors"
                data-testid={`comment-delete-${comment.id}`}
                title="Delete comment"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>
          <p className="text-sm mt-1">{renderMentions(comment.content)}</p>
          <div className="flex items-center gap-3 mt-1.5">
            <button
              onClick={() => onLike(comment.id, comment.is_liked)}
              className={`flex items-center gap-1 text-xs transition-colors ${comment.is_liked ? 'text-red-500' : 'text-muted-foreground hover:text-red-500'}`}
              data-testid={`comment-like-${comment.id}`}
            >
              <Heart className={`w-3 h-3 ${comment.is_liked ? 'fill-current' : ''}`} />
              {comment.likes_count > 0 && <span>{comment.likes_count}</span>}
            </button>
            <button
              onClick={() => onReply({
                ...comment,
                _replyParentId: isReply ? topLevelId : comment.id,
              })}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-honey-amber transition-colors"
              data-testid={`comment-reply-${comment.id}`}
            >
              <Reply className="w-3 h-3" /> reply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const CommentThread = ({ comment, onReply, onLike, onDelete, currentUserId, isAdmin }) => {
  const [showReplies, setShowReplies] = React.useState(false);
  const replies = comment.replies || [];
  const hasMany = replies.length > 3;
  const visibleReplies = hasMany && !showReplies ? replies.slice(0, 2) : replies;

  return (
    <div>
      <SingleComment comment={comment} onReply={onReply} onLike={onLike} onDelete={onDelete} isReply={false} currentUserId={currentUserId} isAdmin={isAdmin} />
      {replies.length > 0 && (
        <div className="space-y-2 mt-2">
          {visibleReplies.map(reply => (
            <SingleComment key={reply.id} comment={reply} onReply={onReply} onLike={onLike} onDelete={onDelete} isReply topLevelId={comment.id} currentUserId={currentUserId} isAdmin={isAdmin} />
          ))}
          {hasMany && !showReplies && (
            <button
              onClick={() => setShowReplies(true)}
              className="ml-8 pl-3 text-xs text-honey-amber hover:underline transition-colors"
              data-testid={`view-replies-${comment.id}`}
            >
              View {replies.length - 2} more {replies.length - 2 === 1 ? 'reply' : 'replies'}
            </button>
          )}
          {hasMany && showReplies && (
            <button
              onClick={() => setShowReplies(false)}
              className="ml-8 pl-3 text-xs text-muted-foreground hover:underline transition-colors"
              data-testid={`hide-replies-${comment.id}`}
            >
              Hide replies
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default CommentThread;
