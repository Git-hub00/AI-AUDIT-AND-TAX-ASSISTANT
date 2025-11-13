import { useEffect, useRef } from 'react'
import { useVoiceRecognition } from './useVoiceRecognition'

interface VoiceCommandsConfig {
  onNameCommand?: (name: string) => void
  onEmailCommand: (email: string) => void
  onPasswordCommand: (password: string) => void
  onConfirmPasswordCommand?: (password: string) => void
  onSignInCommand: () => void
  onSignUpCommand: () => void
  onGoToSignUpCommand: () => void
  onNextCommand: () => void
}

export const useVoiceCommands = (config: VoiceCommandsConfig) => {
  const { isListening, transcript, startListening, stopListening, resetTranscript, isSupported } = useVoiceRecognition()
  const lastTranscriptRef = useRef('')
  const currentFieldRef = useRef<'email' | 'password' | 'confirmPassword' | null>(null)

  useEffect(() => {
    if (transcript && transcript !== lastTranscriptRef.current) {
      lastTranscriptRef.current = transcript
      processVoiceCommand(transcript.toLowerCase())
      
      // Auto reset after processing
      setTimeout(() => {
        resetTranscript()
      }, 1000)
    }
  }, [transcript])

  const processVoiceCommand = (command: string) => {
    console.log('Processing voice command:', command)

    // Navigation commands
    if (command.includes('go to sign up') || command.includes('signup page')) {
      config.onGoToSignUpCommand()
      return
    }

    if (command.includes('sign in') && !command.includes('go to')) {
      config.onSignInCommand()
      return
    }

    if (command.includes('sign up') && !command.includes('go to')) {
      config.onSignUpCommand()
      return
    }

    if (command.includes('next')) {
      config.onNextCommand()
      return
    }

    // Field selection commands
    if (command.startsWith('name')) {
      currentFieldRef.current = 'name'
      const nameText = command.replace('name', '').trim()
      if (nameText && config.onNameCommand) {
        config.onNameCommand(nameText)
      }
      return
    }

    if (command.startsWith('email')) {
      currentFieldRef.current = 'email'
      const emailText = command.replace('email', '').trim()
      if (emailText) {
        config.onEmailCommand(emailText)
      }
      return
    }

    if (command.startsWith('password') && !command.includes('confirm')) {
      currentFieldRef.current = 'password'
      const passwordText = command.replace('password', '').trim()
      if (passwordText) {
        config.onPasswordCommand(passwordText)
      }
      return
    }

    if (command.startsWith('confirm password')) {
      currentFieldRef.current = 'confirmPassword'
      const passwordText = command.replace('confirm password', '').trim()
      if (passwordText && config.onConfirmPasswordCommand) {
        config.onConfirmPasswordCommand(passwordText)
      }
      return
    }

    // Direct input for current field
    if (currentFieldRef.current && command) {
      switch (currentFieldRef.current) {
        case 'name':
          if (config.onNameCommand) {
            config.onNameCommand(command)
          }
          break
        case 'email':
          config.onEmailCommand(command)
          break
        case 'password':
          config.onPasswordCommand(command)
          break
        case 'confirmPassword':
          if (config.onConfirmPasswordCommand) {
            config.onConfirmPasswordCommand(command)
          }
          break
      }
    }
  }

  const setCurrentField = (field: 'name' | 'email' | 'password' | 'confirmPassword' | null) => {
    currentFieldRef.current = field
  }

  return {
    isListening,
    startListening,
    stopListening,
    isSupported,
    setCurrentField,
    currentField: currentFieldRef.current
  }
}