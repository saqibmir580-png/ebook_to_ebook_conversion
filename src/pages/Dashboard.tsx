import React, { useState, useEffect } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
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
  BarChart3,
  FileText,
  ExternalLink,
  RefreshCw,
  FileDown,
  AlertCircle,
  FileJson,
  FileCsv,
  FileCode,
  X,
  Copy
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiService, Project, DashboardStats } from '../services/api';

const API_BASE_URL = 'http://localhost:8000'; // Backend API URL

const Dashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showExportMenu, setShowExportMenu] = useState<number | null>(null);
  const [showXmlPreview, setShowXmlPreview] = useState<number | null>(null);
  const [xmlContent, setXmlContent] = useState<string>('');

  // Load dashboard data
  const loadDashboardData = async (showRefresh = false) => {
    try {
      if (showRefresh) setRefreshing(true);
      else setDashboardLoading(true);
      
      setError(null);
      
      const [projectsData, statsData] = await Promise.all([
        apiService.getProjects(),
        apiService.getDashboardStats()
      ]);
      
      setProjects(projectsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setDashboardLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData();

      // Auto-refresh every 5 seconds for processing projects
      const interval = setInterval(() => {
        // Use a functional update to get the latest projects state
        setProjects(currentProjects => {
          if (currentProjects.some(p => p.status === 'processing' || p.status === 'pending')) {
            loadDashboardData(true);
          }
          return currentProjects;
        });
      }, 5000); // Refresh more frequently for better progress feedback

      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Show loading spinner while checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated (after loading is complete)
  if (!isAuthenticated) {
    return navigate('/login', { replace: true });
  }

  // Handle project view
  const handleViewProject = async (projectId: number) => {
    try {
      const projectDetails = await apiService.getProject(projectId);
      setSelectedProject(projectDetails);
    } catch (err) {
      setError('Failed to load project details');
    }
  };

  // Handle file download
  const handleDownload = async (project: Project, format: 'html' | 'epub' | 'xml' | 'mobi') => {
    try {
      let url: string | undefined;
      
      if (format === 'html') {
        // Use new HTML download endpoint with embedded images
        url = `${API_BASE_URL}/api/v1/downloads/html/${project.id}`;
        console.log(`HTML download: Using new endpoint ${url}`);
        alert(`Using NEW endpoint: ${url}`); // Temporary verification
      } else {
        const urls = {
          epub: project.epub_url,
          xml: project.xml_url,
          mobi: project.mobi_url
        };
        url = urls[format];
        console.log(`${format.toUpperCase()} download: Using URL ${url}`);
      }

      if (!url) {
        console.error(`No URL available for ${format} download`);
        setError(`${format.toUpperCase()} file not available for download`);
        return;
      }

      const token = localStorage.getItem('token');
      console.log(`Making request to: ${url}`);
      console.log(`Auth token present: ${!!token}`);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log(`Response status: ${response.status}`);
      console.log(`Response headers:`, response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Download failed: ${response.status} - ${errorText}`);
        throw new Error(`Failed to download ${format.toUpperCase()} file: ${response.status}`);
      }

      const blob = await response.blob();
      console.log(`Downloaded blob size: ${blob.size} bytes, type: ${blob.type}`);
      
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${project.file_name}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      console.log(`Successfully downloaded ${format.toUpperCase()} file`);
    } catch (err) {
      console.error('Download error:', err);
      setError(`Failed to download ${format.toUpperCase()} file`);
    }
  };

  // Handle project export
  const handleExport = async (project: Project, format: 'json' | 'csv') => {
    try {
      await apiService.exportProject(project.id, format);
      setShowExportMenu(null);
      // Refresh dashboard data to show the newly exported book
      await loadDashboardData(true);
    } catch (err) {
      setError('Export failed');
    }
  };

  // Handle project deletion
  const handleDelete = async (projectId: number) => {
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await apiService.deleteProject(projectId);
      await loadDashboardData();
    } catch (err) {
      setError('Failed to delete project');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      case 'pending': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'processing': return <Clock className="h-4 w-4" />;
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'failed': return <AlertCircle className="h-4 w-4" />;
      default: return null;
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatProcessingTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const handleXmlPreview = async (project: Project) => {
    try {
      const response = await fetch(project.xml_url);
      const xmlContent = await response.text();
      setXmlContent(xmlContent);
      setShowXmlPreview(project.id);
    } catch (err) {
      setError('Failed to load XML preview');
    }
  };

  if (dashboardLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const dashboardStats = [
    {
      label: 'Books Uploaded',
      value: stats?.totalProjects || 0,
      icon: <Upload className="h-6 w-6 text-blue-600" />,
      bg: 'bg-blue-50'
    },
    {
      label: 'Conversions Completed',
      value: stats?.completedProjects || 0,
      icon: <CheckCircle className="h-6 w-6 text-green-600" />,
      bg: 'bg-green-50'
    },
    {
      label: 'In Progress',
      value: stats?.processingProjects || 0,
      icon: <Clock className="h-6 w-6 text-yellow-600" />,
      bg: 'bg-yellow-50'
    },
    {
      label: 'Total Projects',
      value: stats?.totalProjects || 0,
      icon: <BookOpen className="h-6 w-6 text-purple-600" />,
      bg: 'bg-purple-50'
    }
  ];

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
            <div className="mt-4 sm:mt-0 flex items-center space-x-3">
              <button
                onClick={() => loadDashboardData(true)}
                disabled={refreshing}
                className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
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

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-red-800">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {dashboardStats.map((stat, index) => (
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
              <h3 className="text-lg font-semibold">
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
            {projects.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No projects yet</p>
                <Link 
                  to="/convert" 
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Start your first conversion →
                </Link>
              </div>
            ) : (
              projects.map((project) => (
                <div 
                  key={project.id} 
                  className={`px-6 py-4 transition-colors ${
                    project.status === 'processing' 
                      ? 'hover:bg-blue-50 cursor-pointer' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => {
                    if (project.status === 'processing') {
                      // Navigate to processing view
                      navigate(`/convert?processing=${project.id}`);
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <BookOpen className="h-8 w-8 text-gray-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">{project.file_name}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-gray-500">
                            {project.file_type.toUpperCase()} • {formatFileSize(project.file_size)}
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">
                            {new Date(project.created_at).toLocaleDateString()}
                          </span>
                          {project.processing_time && (
                            <>
                              <span className="text-xs text-gray-400">•</span>
                              <span className="text-xs text-gray-500">
                                {formatProcessingTime(project.processing_time)}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      {/* Show progress percentage for processing files */}
                      {project.status === 'processing' && project.progress !== undefined && project.progress > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          <Clock className="h-4 w-4 mr-1" />
                          <span>{project.progress}% Processing</span>
                        </span>
                      ) : (
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                          {getStatusIcon(project.status)}
                          <span className="ml-1 capitalize">{project.status}</span>
                        </span>
                      )}

                      <div className="flex items-center space-x-1">
                        {project.status === 'completed' && (
                          <button 
                            onClick={() => handleViewProject(project.id)}
                            className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        )}
                        
                        <div className="relative">
                          <button 
                            onClick={() => setShowExportMenu(showExportMenu === project.id ? null : project.id)}
                            className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                            title="Download & Export"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          
                          {showExportMenu === project.id && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
                              <div className="py-1">
                                <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b">Download Files</div>
                                {project.html_url && (
                                  <button
                                    onClick={() => handleDownload(project, 'html')}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                  >
                                    <FileText className="h-4 w-4 mr-2" />
                                    HTML
                                  </button>
                                )}
                                {project.epub_url && (
                                  <button
                                    onClick={() => handleDownload(project, 'epub')}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                  >
                                    <BookOpen className="h-4 w-4 mr-2" />
                                    EPUB
                                  </button>
                                )}
                                {project.xml_url && (
                                  <button
                                    onClick={() => handleXmlPreview(project)}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                  >
                                    <Eye className="h-4 w-4 mr-2" />
                                    Preview XML
                                  </button>
                                )}
                                <div className="border-t">
                                  <div className="px-3 py-2 text-xs font-medium text-gray-500">Export Data</div>
                                  {project.json_export_url ? (
                                    <a href={project.json_export_url} download className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between">
                                        <FileDown className="h-4 w-4 mr-2 text-green-600" /> Download JSON
                                    </a>
                                  ) : (
                                    <button onClick={() => handleExport(project, 'json')} className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between">
                                        <FileDown className="h-4 w-4 mr-2" /> Export as JSON
                                    </button>
                                  )}
                                  {project.csv_export_url ? (
                                    <a href={project.csv_export_url} download className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between">
                                        <FileDown className="h-4 w-4 mr-2 text-green-600" /> Download CSV
                                    </a>
                                  ) : (
                                    <button onClick={() => handleExport(project, 'csv')} className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between">
                                        <FileDown className="h-4 w-4 mr-2" /> Export as CSV
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  {(project.status === 'processing' || project.status === 'completed') && project.progress !== undefined && project.progress > 0 && (
                    <div className="mt-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-xs font-medium text-gray-500">Progress</span>
                        <span className="text-xs font-medium text-gray-500">{project.status === 'completed' ? '100%' : `${project.progress}%`}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className={`h-2 rounded-full ${project.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'}`} style={{ width: `${project.status === 'completed' ? '100%' : `${project.progress}%`}` }}></div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
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

        {/* Project Details Modal */}
        {selectedProject && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Project Details</h3>
                  <button
                    onClick={() => setSelectedProject(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedProject.file_name}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Status: <span className="capitalize">{selectedProject.status}</span>
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">File Size:</span>
                    <span className="ml-2 font-medium">{formatFileSize(selectedProject.file_size)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">File Type:</span>
                    <span className="ml-2 font-medium">{selectedProject.file_type.toUpperCase()}</span>
                  </div>
                  {selectedProject.page_count && (
                    <div>
                      <span className="text-gray-600">Pages:</span>
                      <span className="ml-2 font-medium">{selectedProject.page_count}</span>
                    </div>
                  )}
                  {selectedProject.image_count && (
                    <div>
                      <span className="text-gray-600">Images:</span>
                      <span className="ml-2 font-medium">{selectedProject.image_count}</span>
                    </div>
                  )}
                  {selectedProject.formula_count && (
                    <div>
                      <span className="text-gray-600">Formulas:</span>
                      <span className="ml-2 font-medium">{selectedProject.formula_count}</span>
                    </div>
                  )}
                  {selectedProject.processing_time && (
                    <div>
                      <span className="text-gray-600">Processing Time:</span>
                      <span className="ml-2 font-medium">{formatProcessingTime(selectedProject.processing_time)}</span>
                    </div>
                  )}
                </div>

                {selectedProject.error_message && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">{selectedProject.error_message}</p>
                  </div>
                )}

                {selectedProject.status === 'completed' && (
                  <div className="border-t pt-4">
                    <h5 className="font-medium text-gray-900 mb-3">Available Downloads</h5>
                    <div className="space-y-2">
                      {selectedProject.html_url && (
                        <button
                          onClick={() => handleDownload(selectedProject, 'html')}
                          className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 flex items-center justify-between"
                        >
                          <div className="flex items-center">
                            <FileText className="h-5 w-5 text-blue-600 mr-3" />
                            <span>HTML Version</span>
                          </div>
                          <ExternalLink className="h-4 w-4 text-gray-400" />
                        </button>
                      )}
                      {selectedProject.epub_url && (
                        <button
                          onClick={() => handleDownload(selectedProject, 'epub')}
                          className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 flex items-center justify-between"
                        >
                          <div className="flex items-center">
                            <BookOpen className="h-5 w-5 text-green-600 mr-3" />
                            <span>EPUB Version</span>
                          </div>
                          <ExternalLink className="h-4 w-4 text-gray-400" />
                        </button>
                      )}
                      {selectedProject.json_export_url && (
                          <a href={selectedProject.json_export_url} download className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 flex items-center justify-between">
                              <div className="flex items-center">
                                  <FileDown className="h-5 w-5 text-purple-600 mr-3" />
                                  <span>JSON Export</span>
                              </div>
                              <ExternalLink className="h-4 w-4 text-gray-400" />
                          </a>
                      )}
                      {selectedProject.csv_export_url && (
                          <a href={selectedProject.csv_export_url} download className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 flex items-center justify-between">
                              <div className="flex items-center">
                                  <FileDown className="h-5 w-5 text-yellow-600 mr-3" />
                                  <span>CSV Export</span>
                              </div>
                              <ExternalLink className="h-4 w-4 text-gray-400" />
                          </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* XML Preview Modal */}
        {showXmlPreview && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">XML Preview</h3>
                  <button
                    onClick={() => setShowXmlPreview(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-4 flex-1 overflow-y-auto">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">XML Content</h4>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(xmlContent);
                        // You could add a toast notification here
                      }}
                      className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                    >
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </button>
                    <a
                      href={projects.find(p => p.id === showXmlPreview)?.xml_url}
                      download
                      className="flex items-center px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </a>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                    {xmlContent || 'Loading XML content...'}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;