import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { salaService } from '../../services/sala.service';

const CATEGORIAS = ['8va', '7ma', '6ta', '5ta', '4ta', '3ra'];
const TIPOS_JUEGO = ['singles', 'dobles', 'mixto'];

export const CrearSalaScreen = ({ navigation }: any) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    ubicacion: '',
    fecha_hora: '',
    max_jugadores: 4,
    categoria: '8va',
    tipo_juego: 'singles',
    descripcion: '',
  });

  const handleSubmit = async () => {
    if (!formData.nombre || !formData.ubicacion || !formData.fecha_hora) {
      Alert.alert('Error', 'Por favor completa todos los campos obligatorios');
      return;
    }

    setLoading(true);
    try {
      await salaService.crearSala(formData);
      Alert.alert('Éxito', 'Sala creada correctamente', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'No se pudo crear la sala');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Crear Sala</Text>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Información Básica */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Información Básica</Text>
          
          <Input
            label="Nombre de la Sala *"
            value={formData.nombre}
            onChangeText={(text) => setFormData({ ...formData, nombre: text })}
            placeholder="Ej: Partido del Sábado"
          />

          <Input
            label="Ubicación *"
            value={formData.ubicacion}
            onChangeText={(text) => setFormData({ ...formData, ubicacion: text })}
            placeholder="Ej: Club Náutico"
          />

          <Input
            label="Fecha y Hora *"
            value={formData.fecha_hora}
            onChangeText={(text) => setFormData({ ...formData, fecha_hora: text })}
            placeholder="2024-12-25 18:00"
          />

          <Input
            label="Descripción"
            value={formData.descripcion}
            onChangeText={(text) => setFormData({ ...formData, descripcion: text })}
            placeholder="Información adicional..."
            multiline
            numberOfLines={3}
          />
        </View>

        {/* Configuración */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuración</Text>
          
          {/* Máximo de Jugadores */}
          <Text style={styles.label}>Máximo de Jugadores</Text>
          <View style={styles.numberSelector}>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setFormData({ 
                ...formData, 
                max_jugadores: Math.max(2, formData.max_jugadores - 1) 
              })}
            >
              <Text style={styles.numberButtonText}>-</Text>
            </TouchableOpacity>
            <Text style={styles.numberValue}>{formData.max_jugadores}</Text>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setFormData({ 
                ...formData, 
                max_jugadores: Math.min(8, formData.max_jugadores + 1) 
              })}
            >
              <Text style={styles.numberButtonText}>+</Text>
            </TouchableOpacity>
          </View>

          {/* Categoría */}
          <Text style={styles.label}>Categoría</Text>
          <View style={styles.optionsGrid}>
            {CATEGORIAS.map((cat) => (
              <TouchableOpacity
                key={cat}
                style={[
                  styles.optionButton,
                  formData.categoria === cat && styles.optionButtonActive
                ]}
                onPress={() => setFormData({ ...formData, categoria: cat })}
              >
                <Text style={[
                  styles.optionText,
                  formData.categoria === cat && styles.optionTextActive
                ]}>
                  {cat}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Tipo de Juego */}
          <Text style={styles.label}>Tipo de Juego</Text>
          <View style={styles.optionsGrid}>
            {TIPOS_JUEGO.map((tipo) => (
              <TouchableOpacity
                key={tipo}
                style={[
                  styles.optionButton,
                  formData.tipo_juego === tipo && styles.optionButtonActive
                ]}
                onPress={() => setFormData({ ...formData, tipo_juego: tipo })}
              >
                <Text style={[
                  styles.optionText,
                  formData.tipo_juego === tipo && styles.optionTextActive
                ]}>
                  {tipo.charAt(0).toUpperCase() + tipo.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Botón Crear */}
        <Button
          title="Crear Sala"
          onPress={handleSubmit}
          loading={loading}
          variant="accent"
        />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1F2E',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    gap: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3A4558',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 24,
    color: '#E8E9EB',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#E8E9EB',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#E8E9EB',
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#E8E9EB',
    marginBottom: 12,
    marginTop: 16,
  },
  numberSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    backgroundColor: '#0E0F11',
    borderWidth: 1,
    borderColor: '#3A4558',
    borderRadius: 12,
    padding: 16,
  },
  numberButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#0055FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberButtonText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  numberValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#E8E9EB',
    minWidth: 60,
    textAlign: 'center',
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionButton: {
    backgroundColor: '#3A4558',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  optionButtonActive: {
    backgroundColor: '#0055FF',
  },
  optionText: {
    color: '#94A3B8',
    fontWeight: '600',
    fontSize: 14,
  },
  optionTextActive: {
    color: '#E8E9EB',
  },
});
