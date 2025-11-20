import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-4xl text-center">
        <h1 className="text-5xl font-bold text-primary-600 mb-6">
          MyTravel
        </h1>
        <p className="text-xl text-secondary-600 mb-8">
          AI-Powered Vietnam Travel Planning Assistant
        </p>
        <p className="text-lg text-secondary-500 mb-12">
          Plan your perfect Vietnam trip with intelligent AI assistance.
          Discover accommodations, restaurants, transportation, and activities
          tailored to your preferences.
        </p>

        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Get Started
          </Link>
          <Link
            href="/register"
            className="px-8 py-3 border border-primary-600 text-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-medium"
          >
            Sign Up
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">Smart Recommendations</h3>
            <p className="text-secondary-500">
              Get personalized suggestions for hotels, restaurants, and attractions
            </p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">AI Chat Assistant</h3>
            <p className="text-secondary-500">
              Plan your trip through natural conversation with our AI
            </p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">Budget Tracking</h3>
            <p className="text-secondary-500">
              Keep track of expenses and stay within your budget
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
