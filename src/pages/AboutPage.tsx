import React from 'react';
import { Users, Award, Globe, Heart } from 'lucide-react';

const AboutPage: React.FC = () => {
  const stats = [
    { label: 'Books Converted', value: '50,000+' },
    { label: 'Happy Users', value: '10,000+' },
    { label: 'Countries Served', value: '120+' },
    { label: 'Accuracy Rate', value: '99.9%' }
  ];

  const team = [
    {
      name: 'Sarah Johnson',
      role: 'CEO & Founder',
      image: 'https://images.pexels.com/photos/3184360/pexels-photo-3184360.jpeg?auto=compress&cs=tinysrgb&w=300',
    },
    {
      name: 'Michael Chen',
      role: 'CTO',
      image: 'https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=300',
    },
    {
      name: 'Emily Rodriguez',
      role: 'Head of Product',
      image: 'https://images.pexels.com/photos/3184302/pexels-photo-3184302.jpeg?auto=compress&cs=tinysrgb&w=300',
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-6">
            Transforming Publishing with AI
          </h1>
          <p className="text-xl sm:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
            We're on a mission to make professional e-book creation accessible to everyone, 
            from individual authors to large publishing houses.
          </p>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold text-blue-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-600 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
                Our Story
              </h2>
              <div className="prose prose-lg text-gray-700 space-y-4">
                <p>
                  Founded in 2023, EBookConverter was born from a simple frustration: converting documents 
                  into professional e-books was too complicated, time-consuming, and expensive.
                </p>
                <p>
                  Our team of AI researchers, publishing experts, and software engineers came together 
                  to build a platform that democratizes e-book creation. We believe that great content 
                  should be accessible to everyone, regardless of technical expertise.
                </p>
                <p>
                  Today, we're proud to serve authors, educators, businesses, and publishers worldwide, 
                  helping them transform their ideas into beautifully formatted digital publications.
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <Users className="h-8 w-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">User-Centric</h3>
                <p className="text-gray-600 text-sm">Every feature is designed with our users in mind</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-md">
                <Award className="h-8 w-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Excellence</h3>
                <p className="text-gray-600 text-sm">We strive for perfection in every conversion</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-md">
                <Globe className="h-8 w-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Global Reach</h3>
                <p className="text-gray-600 text-sm">Supporting creators worldwide</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-md">
                <Heart className="h-8 w-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Passion</h3>
                <p className="text-gray-600 text-sm">We love what we do and it shows</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Meet Our Team
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The passionate individuals behind EBookConverter
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {team.map((member, index) => (
              <div key={index} className="text-center group">
                <div className="relative mb-4">
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-32 h-32 rounded-full mx-auto object-cover group-hover:scale-105 transition-transform"
                  />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-1">{member.name}</h3>
                <p className="text-blue-600 font-medium">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-8">
            Our Values
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Innovation</h3>
              <p className="text-blue-100">
                We constantly push the boundaries of what's possible with AI and automation
              </p>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Accessibility</h3>
              <p className="text-blue-100">
                Professional-grade tools should be available to everyone, not just big corporations
              </p>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Quality</h3>
              <p className="text-blue-100">
                Every conversion meets the highest standards of accuracy and formatting
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;