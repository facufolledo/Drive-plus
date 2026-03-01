import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/auth.service';

const CATEGORIAS = ['8va', '7ma', '6ta', '5ta', '4ta', '3ra'];
const MANOS = ['derecha', 'izquierda', 'ambas'];
const POSICIONES = ['drive', 'reves', 'indiferente'];

export const EditarPerfilScreen = ({ navigation }: any) => {
  const { usuario, setUsuario } = useAuthStore();
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    nombre: usuario?.nombre || '',
    apellido: usuario?.apellido || '',
    telefono: usuario?.telefono || '',
    ciudad: usuario?.ciudad || '',
    categoria_inicial: usuario?.categoria_inicial || '8va',
    mano_habil: usuario?.mano_habil || 'derecha',
    posicion_preferida: usuario?.posicion_preferida || 'indiferente',
  });

  const handleSubmit = async () => {
    if (!formData.nombre || !formData.apellido) {
      Alert.alert('Error', 'Nombre y apellido son obligatorios');
      return;
    }

    setLoading(true);
    try {
      const usuarioActualizado = await authService.actualizarPerfil(formData);
      setUsuario(usuarioActualizado);
      Alert.alert('Éxito', 'Perfil actualizado correctamente', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'No se pudo actualizar el perfil');
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
        <Text style={styles.title}>Editar Perfil</Text>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Avatar */}
        <View style={styles.avatarSection}>
          <View style={styles.avatarLarge}>
            <Text style={styles.avatarText}>
              {formData.nombre?.charAt(0) || 'U'}
            </Text>
          </View>
          <TouchableOpacity style={styles.changeAvatarButton}>
            <Text style={styles.changeAvatarText}>Cambiar foto</Text>
          </TouchableOpacity>
        </View>

        {/* Datos Personales */}
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
            label="Teléfono"
            value={formData.telefono}
            onChangeText={(text) => setFormData({ ...formData, telefono: text })}
            placeholder="+54 9 11 1234-5678"
            keyboardType="phone-pad"
          />

          <Input
            label="Ciudad"
            value={formData.ciudad}
            onChangeText={(text) => setFormData({ ...formData, ciudad: text })}
            placeholder="Buenos Aires"
          />
        </View>

        {/* Datos Deportivos */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Datos Deportivos</Text>
          
          {/* Categoría */}
          <Text style={styles.label}>Categoría</Text>
          <View style={styles.optionsGrid}>
            {CATEGORIAS.map((cat) => (
              <TouchableOpacity
                key={cat}
                style={[
                  styles.optionButton,
                  formData.categoria_inicial === cat && styles.optionButtonActive
                ]}
                onPress={() => setFormData({ ...formData, categoria_inicial: cat })}
              >
                <Text style={[
                  styles.optionText,
                  formData.categoria_inicial === cat && styles.optionTextActive
                ]}>
                  {cat}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Mano Hábil */}
          <Text style={styles.label}>Mano Hábil</Text>
          <View style={styles.optionsRow}>
            {MANOS.map((mano) => (
              <TouchableOpacity
                key={mano}
                style={[
                  styles.optionButtonLarge,
                  formData.mano_habil === mano && styles.optionButtonActive
                ]}
                onPress={() => setFormData({ ...formData, mano_habil: mano })}
              >
                <Text style={[
                  styles.optionText,
                  formData.mano_habil === mano && styles.optionTextActive
                ]}>
                  {mano.charAt(0).toUpperCase() + mano.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Posición Preferida */}
          <Text style={styles.label}>Posición Preferida</Text>
          <View style={styles.optionsRow}>
            {POSICIONES.map((pos) => (
              <TouchableOpacity
                key={pos}
                style={[
                  styles.optionButtonLarge,
                  formData.posicion_preferida === pos && styles.optionButtonActive
                ]}
                onPress={() => setFormData({ ...formData, posicion_preferida: pos })}
              >
                <Text style={[
                  styles.optionText,
                  formData.posicion_preferida === pos && styles.optionTextActive
                ]}>
                  {pos.charAt(0).toUpperCase() + pos.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Botones */}
        <View style={styles.buttonsContainer}>
          <Button
            title="Guardar Cambios"
            onPress={handleSubmit}
            loading={loading}
            variant="accent"
          />
          <Button
            title="Cancelar"
            onPress={() => navigation.goBack()}
            variant="ghost"
          />
        </View>
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
  avatarSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  avatarLarge: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#0055FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 40,
    fontWeight: 'bold',
  },
  changeAvatarButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  changeAvatarText: {
    color: '#0055FF',
    fontSize: 14,
    fontWeight: '600',
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
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  optionButton: {
    backgroundColor: '#3A4558',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  optionButtonLarge: {
    flex: 1,
    backgroundColor: '#3A4558',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
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
  buttonsContainer: {
    gap: 12,
  },
});
