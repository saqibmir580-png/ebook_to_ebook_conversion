import React, { useEffect } from 'react';
import { toast } from 'react-toastify';

const ToastTest: React.FC = () => {
  useEffect(() => {
    // Show a test toast when component mounts
    toast.success('Test toast from ToastTest component', {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
    });
    
    // Log toast function info
    console.log('Toast function type:', typeof toast);
    console.log('Toast container in DOM:', document.querySelector('.Toastify'));
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Toast Test Component</h2>
      <button 
        onClick={() => {
          toast.success('Button click toast!', {
            position: "top-right"
          });
        }}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        Show Test Toast
      </button>
    </div>
  );
};

export default ToastTest;
