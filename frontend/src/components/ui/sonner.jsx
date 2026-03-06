import { Toaster as Sonner, toast } from "sonner"

const Toaster = ({ ...props }) => {
  return (
    <Sonner
      className="toaster group"
      position="top-center"
      offset="96px"
      toastOptions={{
        unstyled: true,
        classNames: {
          toast: "honey-toast",
          title: "honey-toast-title",
          description: "honey-toast-desc",
        },
      }}
      icons={{
        success: <span className="honey-toast-icon">🍯</span>,
        error: <span className="honey-toast-icon">🐝</span>,
        info: <span className="honey-toast-icon">🎵</span>,
        warning: <span className="honey-toast-icon">🐝</span>,
      }}
      {...props}
    />
  );
}

export { Toaster, toast }
