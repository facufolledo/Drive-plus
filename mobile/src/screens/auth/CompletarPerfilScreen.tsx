import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/auth.service';

const CATEGORIAS = ['8va', '7ma', '6ta', '5ta', '4ta', '3ra'];

export const CompletarPerfilScreen = ({ navigation }: any) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setUsuario = useAuthStore((state) => state.setUsuario);
  
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    dni: '',
    fecha_nacimiento: '',
    genero: 'masculino',
    categoria_inicial: '8va',
    mano_habil: 'derecha',
    posicion_preferida: 'indiferente',
    telefono: '',
    ciudad: ''
  });

  const handleSubmit = async () => {
    setError('');
    
    if (!formData.nombre || !formData.apellido || !formData.dni || !formData.fecha_nacimiento) {
      setError('Por favor completa todos los campos obligatorios');
      return;
    }

    setLoading(true);
    try {
      const usuario = await authService.completarPerfil(formData);
      setUsuario(usuario);
    } catch (err: any) {
      setError(err.message || 'Error al completar el perfil');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Completá tu Perfil</Text>
        <Text style={styles.subtitle}>Necesitamos algunos datos para crear tu cuenta</Text>
      </View>

      {error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Datos Personales</Text>
        
        <Input
          label="Nombre *"
          value={formData.nombre}
          onChangeText={(text) => setFormData({ ...formData, nombre: text })}
          placeholder="Juan"
        />

        <Input
          label="Apellido *"
          value={formData.apellido}
          onChangeText={(text) => setFormData({ ...formData, apellido: text })}
          placeholder="Pérez"
        />

        <Input
          label="DNI *"
          value={formData.dni}
          onChangeText={(text) => setFormData({ ...formData, dni: text })}
          placeholder="12345678"
          keyboardType="numeric"
        />

        <Input
          label="Fecha de Nacimiento *"
          value={formData.fecha_nacimiento}
          onChangeText={(text) => setFormData({ ...formData, fecha_nacimiento: text })}
          placeholder="1990-01-01"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Categoría Inicial</Text>
        <View style={styles.categoriaContainer}>
          {CATEGORIAS.map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[
                styles.categoriaButton,
                formData.categoria_inicial === cat && styles.categoriaButtonActive
              ]}
              onPress={() => setFormData({ ...formData, categoria_inicial: cat })}
            >
              <Text style={[
                styles.categoriaText,
                formData.categoria_inicial === cat && styles.categoriaTextActive
              ]}>
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <Button
        title="Completar Registro"
        onPress={handleSubmit}
        loading={loading}
        variant="accent"
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1F2E',
  },
  content: {
    padding: 24,
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#E8E9EB',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94A3B8',
  },
  errorContainer: {
    backgroundColor: 'rgba(255, 0, 85, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 0, 85, 0.5)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#FF0055',
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#E8E9EB',
    marginBottom: 16,
  },
  categoriaContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoriaButton: {
    backgroundColor: '#3A4558',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 60,
    alignItems: 'center',
  },
  categoriaButtonActive: {
    backgroundColor: '#FFD700',
  },
  categoriaText: {
    color: '#94A3B8',
    fontWeight: '600',
  },
  categoriaTextActive: {
    color: '#0E0F11',
  },
});
