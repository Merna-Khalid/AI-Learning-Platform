import api from './api';

export const getCourses = async () => {
  try {
    const response = await api.get('/courses/');
    return response.data;
  } catch (error) {
    console.error('Error fetching courses:', error);
    throw error;
  }
};

export const createCourse = async (courseData) => {
  try {
    const response = await api.post('/courses/', courseData);
    return response.data;
  } catch (error) {
    console.error('Error creating course:', error);
    throw error;
  }
};

export const uploadCourseMaterial = async (courseId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post(`/courses/${courseId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading course material:', error);
    throw error;
  }
};


export const uploadBatchMaterials = async (courseId, files) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  
  try {
    const response = await api.post(`/courses/${courseId}/upload-batch`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading batch materials:', error);
    throw error;
  }
};

export const getCourseMaterials = async (courseId) => {
  try {
    console.log(`Fetching materials for course ${courseId}`);
    const response = await api.get(`/courses/${courseId}/materials`);
    console.log('Materials response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching course materials:', error);

    if (error.response?.status === 404) {
      throw new Error('Course not found');
    } else if (error.response?.status === 500) {
      throw new Error('Server error while fetching materials');
    } else if (error.code === 'NETWORK_ERROR') {
      throw new Error('Cannot connect to server');
    }
    
    throw new Error(error.message || 'Failed to load materials');
  }
};

export const getCourseTopics = async (courseId) => {
  try {
    const response = await api.get(`/topics/${courseId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching course topics:', error);
    throw error;
  }
};