'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { User, Lock, Mail } from 'lucide-react';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const supabase = createClient();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      setLoading(false);
      return;
    }

    try {
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
          data: {
            first_name: firstName,
            last_name: lastName,
          },
        },
      });

      if (authError) throw authError;

      // Create profile in profiles table
      if (authData.user) {
        const { error: profileError } = await supabase
          .from('profiles')
          .insert({
            id: authData.user.id,
            first_name: firstName,
            last_name: lastName,
          });

        if (profileError) {
          console.error('Error creating profile:', profileError);
          // Continue anyway - profile can be created later
        }
      }

      router.push('/');
      router.refresh();
    } catch (error: any) {
      setError(error.message || 'Erreur lors de la création du compte');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#FAFAFA] to-[#F5F5F5] px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-[#1A1A1A] mb-2" style={{ letterSpacing: '-0.03em' }}>
            Quantis
          </h1>
          <p className="text-sm text-[#737373]">Créer un nouveau compte</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg border border-[#E5E5E5] shadow-sm p-8">
          <form onSubmit={handleSignup} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            {/* First Name */}
            <div>
              <label htmlFor="firstName" className="block text-sm font-medium text-[#1A1A1A] mb-2">
                Prénom
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#737373]" />
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-[#E5E5E5] rounded-md focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-[#1A1A1A]"
                  placeholder="Votre prénom"
                />
              </div>
            </div>

            {/* Last Name */}
            <div>
              <label htmlFor="lastName" className="block text-sm font-medium text-[#1A1A1A] mb-2">
                Nom
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#737373]" />
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-[#E5E5E5] rounded-md focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-[#1A1A1A]"
                  placeholder="Votre nom"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#1A1A1A] mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#737373]" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-[#E5E5E5] rounded-md focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-[#1A1A1A]"
                  placeholder="votre@email.com"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#1A1A1A] mb-2">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#737373]" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full pl-10 pr-4 py-2.5 border border-[#E5E5E5] rounded-md focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-[#1A1A1A]"
                  placeholder="••••••••"
                />
              </div>
              <p className="mt-1 text-xs text-[#737373]">Minimum 6 caractères</p>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#1A1A1A] mb-2">
                Confirmer le mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#737373]" />
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-[#E5E5E5] rounded-md focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-[#1A1A1A]"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1A1A1A] text-white py-2.5 rounded-md font-medium hover:bg-[#2A2A2A] transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Création...' : 'Créer un compte'}
            </button>
          </form>

          {/* Login link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-[#737373]">
              Déjà un compte ?{' '}
              <a href="/login" className="text-[#1A1A1A] font-medium hover:underline">
                Se connecter
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

