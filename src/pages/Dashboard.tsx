import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Upload, 
  BookOpen, 
  CheckCircle, 
  Clock, 
  MoreVertical, 
  Eye, 
  Download,
  Trash2,
  Plus,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface ConversionProject {
  id: string;
  name: string;
  status: 'processing' | 'completed' | 'failed';
  createdAt: string;
  fileType: string;
  outputFormat: string;
  progress?: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [projects] = useState<ConversionProject[]>([
    {
      id: '1',
      name: 'My First Novel.pdf',
      status: 'completed',
      createdAt: '2025-01-19',
      fileType: 'PDF',
      outputFormat: 'EPUB'
    },
    {
      id: '2',
      name: 'Technical Manual.docx',
      status: 'processing',
      createdAt: '2025-01-19',
      fileType: 'DOCX',
      outputFormat: 'HTML',
      progress: 65
    },
    {
      id: '3',
      name: 'Recipe Book.pdf',
      status: 'completed',
      createdAt: '2025-01-18',
      fileType: 'PDF',
      outputFormat: 'EPUB'
    },
    {
      id: '4',
      name: 'Research Paper.txt',
      status: 'failed',
      createdAt: '2025-01-18',
      fileType: 'TXT',
      outputFormat: 'PDF'
    }
  ]);

  const stats = [
    {
      label: 'Books Uploaded',
      value: user?.booksUploaded || 0,
      icon: <Upload className="h-6 w-6 text-blue-600" />,
      bg: 'bg-blue-50'
    },
    {
      label: 'Conversions Completed',
      value: user?.conversionsCompleted || 0,
      icon: <CheckCircle className="h-6 w-6 text-green-600" />,
      bg: 'bg-green-50'
    },
    {
      label: 'In Progress',
      value: projects.filter(p => p.status === 'processing').length,
      icon: <Clock className="h-6 w-6 text-yellow-600" />,
      bg: 'bg-yellow-50'
    },
    {
      label: 'Total Projects',
      value: projects.length,
      icon: <BookOpen className="h-6 w-6 text-purple-600" />,
      bg: 'bg-purple-50'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'processing': return <Clock className="h-4 w-4" />;
      case 'failed': return <Trash2 className="h-4 w-4" />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome back, {user?.name}!</h1>
              <p className="text-gray-600 mt-1">Manage your e-book conversion projects</p>
            </div>
            <div className="mt-4 sm:mt-0">
              <Link
                to="/convert"
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-colors group"
              >
                <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform" />
                New Conversion
              </Link>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bg}`}>
                  {stat.icon}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Subscription Status */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 mb-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-1">
                {user?.subscription?.charAt(0).toUpperCase() + user?.subscription?.slice(1)} Plan
              </h3>
              <p className="text-blue-100">
                {user?.subscription === 'free' 
                  ? 'Upgrade to unlock unlimited conversions' 
                  : 'Enjoying unlimited conversions and advanced features'
                }
              </p>
            </div>
            {user?.subscription === 'free' && (
              <Link
                to="/subscription"
                className="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors"
              >
                Upgrade Now
              </Link>
            )}
          </div>
        </div>

        {/* Recent Projects */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Recent Projects</h2>
              <button className="text-blue-600 hover:text-blue-700 transition-colors">
                <BarChart3 className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {projects.map((project) => (
              <div key={project.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <BookOpen className="h-8 w-8 text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{project.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs text-gray-500">{project.fileType} → {project.outputFormat}</span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-500">{project.createdAt}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {getStatusIcon(project.status)}
                      <span className="ml-1 capitalize">{project.status}</span>
                    </span>

                    {project.status === 'processing' && project.progress && (
                      <div className="w-24">
                        <div className="bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${project.progress}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500 mt-1">{project.progress}%</span>
                      </div>
                    )}

                    <div className="flex items-center space-x-1">
                      {project.status === 'completed' && (
                        <>
                          <button className="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                            <Eye className="h-4 w-4" />
                          </button>
                          <button className="p-1 text-gray-400 hover:text-green-600 transition-colors">
                            <Download className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors">
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="px-6 py-4 bg-gray-50 text-center">
            <Link 
              to="/convert" 
              className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              Start a new conversion project →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;