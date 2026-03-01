import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { torneoService } from '../../services/torneo.service';

const CATEGORIAS = ['8va', '7ma', '6ta', '5ta', '4ta', '3ra'];
const FORMATOS = ['eliminacion_simple', 'eliminacion_doble', 'round_robin', 'grupos'];
const GENEROS = ['masculino', 'femenino', 'mixto'];

export const CrearTorneoScreen = ({ navigation }: any) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    fecha_inicio: '',
    fecha_fin: '',
    max_participantes: 8,
    categoria: '8va',
    formato: 'eliminacion_simple',
    genero: 'mixto',
    ubicacion: '',
  });

  const handleSubmit = async () => {
    // Validaciones
    if (!formData.nombre || !formData.fecha_inicio || !formData.fecha_fin || !formData.ubicacion) {
      Alert.alert('Error', 'Por favor completa todos los campos obligatorios');
      return;
    }

    // Validar que fecha_fin sea posterior a fecha_inicio
    if (new Date(formData.fecha_fin) <= new Date(formData.fecha_inicio)) {
      Alert.alert('Error', 'La fecha de fin debe ser posterior a la fecha de inicio');
      return;
    }

    setLoading(true);
    try {
      await torneoService.crearTorneo(formData);
      Alert.alert('Éxito', 'Torneo creado correctamente', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'No se pudo crear el torneo');
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
        <Text style={styles.title}>Crear Torneo</Text>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Información Básica */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Información Básica</Text>
          
          <Input
            label="Nombre del Torneo *"
            value={formData.nombre}
            onChangeText={(text) => setFormData({ ...formData, nombre: text })}
            placeholder="Ej: Torneo de Verano 2024"
          />

          <Input
            label="Ubicación *"
            value={formData.ubicacion}
            onChangeText={(text) => setFormData({ ...formData, ubicacion: text })}
            placeholder="Ej: Club Náutico"
          />

          <Input
            label="Fecha de Inicio *"
            value={formData.fecha_inicio}
            onChangeText={(text) => setFormData({ ...formData, fecha_inicio: text })}
            placeholder="2024-12-25"
          />

          <Input
            label="Fecha de Fin *"
            value={formData.fecha_fin}
            onChangeText={(text) => setFormData({ ...formData, fecha_fin: text })}
            placeholder="2024-12-26"
          />

          <Input
            label="Descripción"
            value={formData.descripcion}
            onChangeText={(text) => setFormData({ ...formData, descripcion: text })}
            placeholder="Información adicional sobre el torneo..."
            multiline
            numberOfLines={4}
          />
        </View>

        {/* Configuración */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuración</Text>
          
          {/* Máximo de Participantes */}
          <Text style={styles.label}>Máximo de Participantes</Text>
          <View style={styles.numberSelector}>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setFormData({ 
                ...formData, 
                max_participantes: Math.max(4, formData.max_participantes - 2) 
              })}
            >
              <Text style={styles.numberButtonText}>-</Text>
            </TouchableOpacity>
            <Text style={styles.numberValue}>{formData.max_participantes}</Text>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setFormData({ 
                ...formData, 
                max_participantes: Math.min(64, formData.max_participantes + 2) 
              })}
            >
              <Text style={styles.numberButtonText}>+</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.hint}>Debe ser potencia de 2 (4, 8, 16, 32, 64)</Text>

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

          {/* Formato */}
          <Text style={styles.label}>Formato del Torneo</Text>
          <View style={styles.formatoContainer}>
            {FORMATOS.map((formato) => (
              <TouchableOpacity
                key={formato}
                style={[
                  styles.formatoButton,
                  formData.formato === formato && styles.formatoButtonActive
                ]}
                onPress={() => setFormData({ ...formData, formato })}
              >
                <View style={styles.formatoContent}>
                  <Text style={styles.formatoIcon}>
                    {formato === 'eliminacion_simple' ? '🏆' :
                     formato === 'eliminacion_doble' ? '🎯' :
                     formato === 'round_robin' ? '🔄' : '👥'}
                  </Text>
                  <View style={styles.formatoInfo}>
                    <Text style={[
                      styles.formatoTitle,
                      formData.formato === formato && styles.formatoTitleActive
                    ]}>
                      {formato === 'eliminacion_simple' ? 'Eliminación Simple' :
                       formato === 'eliminacion_doble' ? 'Eliminación Doble' :
                       formato === 'round_robin' ? 'Round Robin' : 'Por Grupos'}
                    </Text>
                    <Text style={styles.formatoDesc}>
                      {formato === 'eliminacion_simple' ? 'Pierdes y quedas eliminado' :
                       formato === 'eliminacion_doble' ? 'Dos oportunidades' :
                       formato === 'round_robin' ? 'Todos contra todos' : 'Fase de grupos + eliminación'}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          {/* Género */}
          <Text style={styles.label}>Género</Text>
          <View style={styles.generoContainer}>
            {GENEROS.map((gen) => (
              <TouchableOpacity
                key={gen}
                style={[
                  styles.generoButton,
                  formData.genero === gen && styles.generoButtonActive
                ]}
                onPress={() => setFormData({ ...formData, genero: gen })}
              >
                <Text style={styles.generoIcon}>
                  {gen === 'masculino' ? '♂' : gen === 'femenino' ? '♀' : '⚥'}
                </Text>
                <Text style={[
                  styles.generoText,
                  formData.genero === gen && styles.generoTextActive
                ]}>
                  {gen.charAt(0).toUpperCase() + gen.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Botón Crear */}
        <Button
          title="Crear Torneo"
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
  hint: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 8,
    fontStyle: 'italic',
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
    backgroundColor: '#FFD700',
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberButtonText: {
    color: '#0E0F11',
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
    backgroundColor: '#FFD700',
  },
  optionText: {
    color: '#94A3B8',
    fontWeight: '600',
    fontSize: 14,
  },
  optionTextActive: {
    color: '#0E0F11',
  },
  formatoContainer: {
    gap: 12,
  },
  formatoButton: {
    backgroundColor: '#0E0F11',
    borderWidth: 2,
    borderColor: '#3A4558',
    borderRadius: 12,
    padding: 16,
  },
  formatoButtonActive: {
    borderColor: '#FFD700',
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
  },
  formatoContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  formatoIcon: {
    fontSize: 32,
  },
  formatoInfo: {
    flex: 1,
  },
  formatoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#E8E9EB',
    marginBottom: 4,
  },
  formatoTitleActive: {
    color: '#FFD700',
  },
  formatoDesc: {
    fontSize: 14,
    color: '#94A3B8',
  },
  generoContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  generoButton: {
    flex: 1,
    backgroundColor: '#3A4558',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  generoButtonActive: {
    backgroundColor: '#0055FF',
  },
  generoIcon: {
    fontSize: 20,
    color: '#E8E9EB',
  },
  generoText: {
    color: '#94A3B8',
    fontWeight: '600',
  },
  generoTextActive: {
    color: '#E8E9EB',
  },
});
