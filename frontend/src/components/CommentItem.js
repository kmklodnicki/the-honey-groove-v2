import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Reply } from 'lucide-react';
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

const SingleComment = ({ comment, onReply, onLike, isReply }) => (
  <div className={isReply ? 'ml-8' : ''} data-testid={`comment-${comment.id}`}>
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
          {!isReply && (
            <button
              onClick={() => onReply(comment)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-honey-amber transition-colors"
              data-testid={`comment-reply-${comment.id}`}
            >
              <Reply className="w-3 h-3" /> reply
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

const CommentThread = ({ comment, onReply, onLike }) => (
  <div>
    <SingleComment comment={comment} onReply={onReply} onLike={onLike} isReply={false} />
    {comment.replies && comment.replies.length > 0 && (
      <div className="space-y-2 mt-2">
        {comment.replies.map(reply => (
          <SingleComment key={reply.id} comment={reply} onReply={onReply} onLike={onLike} isReply />
        ))}
      </div>
    )}
  </div>
);

export default CommentThread;
