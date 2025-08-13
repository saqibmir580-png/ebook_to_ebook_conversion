import React from 'react';
import { Check, Star, Zap, Crown } from 'lucide-react';

const SubscriptionPage: React.FC = () => {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      icon: <Star className="h-6 w-6" />,
      features: [
        '5 conversions per month',
        'Basic file formats (PDF, JPG)',
        'Standard text extraction',
        'Community support',
        'Basic export formats'
      ],
      color: 'from-gray-500 to-gray-600',
      buttonColor: 'bg-gray-600 hover:bg-gray-700'
    },
    {
      name: 'Premium',
      price: '$19',
      period: 'month',
      icon: <Zap className="h-6 w-6" />,
      popular: true,
      features: [
        'Unlimited conversions',
        'All file formats supported',
        'AI-powered text extraction',
        'Advanced spell checking',
        'XML validation',
        'Priority support',
        'All export formats',
        'Batch processing'
      ],
      color: 'from-blue-600 to-indigo-600',
      buttonColor: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      name: 'Enterprise',
      price: '$99',
      period: 'month',
      icon: <Crown className="h-6 w-6" />,
      features: [
        'Everything in Premium',
        'White-label solution',
        'Custom integrations',
        'Dedicated support manager',
        'SLA guarantee',
        'Custom export formats',
        'Team collaboration',
        'Advanced analytics'
      ],
      color: 'from-purple-600 to-pink-600',
      buttonColor: 'bg-purple-600 hover:bg-purple-700'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Select the perfect plan for your e-book conversion needs. All plans include core features with flexible pricing.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-white rounded-2xl shadow-lg overflow-hidden ${
                plan.popular ? 'ring-2 ring-blue-600 scale-105' : ''
              } hover:shadow-xl transition-all duration-300`}
            >
              {plan.popular && (
                <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-center py-2 text-sm font-semibold">
                  Most Popular
                </div>
              )}
              
              <div className="p-8">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r ${plan.color} text-white mb-4`}>
                  {plan.icon}
                </div>
                
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                  {plan.price !== '$0' && <span className="text-gray-600">/{plan.period}</span>}
                </div>
                
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center">
                      <Check className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <button
                  className={`w-full py-3 px-4 rounded-lg text-white font-semibold transition-colors ${plan.buttonColor}`}
                >
                  {plan.name === 'Free' ? 'Get Started' : `Choose ${plan.name}`}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Frequently Asked Questions
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Can I change my plan anytime?</h3>
              <p className="text-gray-600">Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">What file formats are supported?</h3>
              <p className="text-gray-600">We support PDF, JPG, PNG, DOCX, TXT, and many other popular document formats.</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Is there a free trial?</h3>
              <p className="text-gray-600">The Free plan allows you to try our core features with 5 conversions per month.</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">How does billing work?</h3>
              <p className="text-gray-600">Billing is monthly for Premium and Enterprise plans. You can cancel anytime.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;