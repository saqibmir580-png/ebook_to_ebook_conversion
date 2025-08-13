import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Upload, Edit, Download, CheckCircle, Star, Zap } from 'lucide-react';

const HomePage: React.FC = () => {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-6xl font-bold mb-6">
              Transform Documents into
              <span className="block text-yellow-300">Beautiful E-Books</span>
            </h1>
            <p className="text-xl sm:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
              AI-powered conversion platform that turns your PDFs, images, and documents into 
              professional e-books with advanced editing and validation tools.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                to="/register"
                className="bg-yellow-400 text-black px-8 py-4 rounded-lg font-semibold hover:bg-yellow-300 transition-colors flex items-center space-x-2 group"
              >
                <span>Start Converting Now</span>
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/about"
                className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
              >
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Simple three-step process to convert your documents into professional e-books
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center group">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-blue-200 transition-colors">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Upload Documents</h3>
              <p className="text-gray-600">
                Upload PDF, JPG, or other document formats with drag-and-drop simplicity
              </p>
            </div>

            <div className="text-center group">
              <div className="bg-indigo-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-indigo-200 transition-colors">
                <Edit className="h-8 w-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Edit & Validate</h3>
              <p className="text-gray-600">
                AI-powered spell checking, XML validation, and professional editing tools
              </p>
            </div>

            <div className="text-center group">
              <div className="bg-emerald-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-emerald-200 transition-colors">
                <Download className="h-8 w-8 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Export & Share</h3>
              <p className="text-gray-600">
                Download in multiple formats: EPUB, HTML, PDF, and more
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to create professional e-books
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: <Zap className="h-6 w-6" />,
                title: "AI-Powered Text Extraction",
                description: "Advanced OCR technology extracts text with 99.9% accuracy"
              },
              {
                icon: <CheckCircle className="h-6 w-6" />,
                title: "Smart Spell Checking",
                description: "AI identifies and suggests corrections for spelling mistakes"
              },
              {
                icon: <Star className="h-6 w-6" />,
                title: "XML Validation",
                description: "Oxygen-like editor with DTD and ENT rules validation"
              },
              {
                icon: <Edit className="h-6 w-6" />,
                title: "Visual Editor",
                description: "Side-by-side editing with live preview"
              },
              {
                icon: <Download className="h-6 w-6" />,
                title: "Multiple Export Formats",
                description: "EPUB, HTML, PDF, MOBI, and more"
              },
              {
                icon: <Upload className="h-6 w-6" />,
                title: "Bulk Processing",
                description: "Convert multiple documents simultaneously"
              }
            ].map((feature, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                <div className="text-blue-600 mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Ready to Start Converting?
          </h2>
          <p className="text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Join thousands of authors and publishers who trust our platform
          </p>
          <Link
            to="/register"
            className="bg-yellow-400 text-black px-8 py-4 rounded-lg font-semibold hover:bg-yellow-300 transition-colors inline-flex items-center space-x-2 group"
          >
            <span>Get Started Free</span>
            <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;