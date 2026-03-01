import { motion } from 'framer-motion';

interface RatingProgressBarProps {
  currentRating: number;
  minRating?: number;
  maxRating?: number;
  categoria?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const getCategoriaColor = (rating: number) => {
  if (rating < 900) return { from: '#CD7F32', to: '#8B4513', name: '8va' };
  if (rating < 1100) return { from: '#C0C0C0', to: '#808080', name: '7ma' };
  if (rating < 1300) return { from: '#FFD700', to: '#FFA500', name: '6ta' };
  if (rating < 1500) return { from: '#E5E4E2', to: '#B0B0B0', name: '5ta' };
  if (rating < 1700) return { from: '#B9F2FF', to: '#00CED1', name: '4ta' };
  return { from: '#9B59B6', to: '#E91E63', name: '3ra' };
};

const getNextCategoriaThreshold = (rating: number) => {
  if (rating < 900) return 900;
  if (rating < 1100) return 1100;
  if (rating < 1300) return 1300;
  if (rating < 1500) return 1500;
  if (rating < 1700) return 1700;
  return 2000;
};

const getPreviousCategoriaThreshold = (rating: number) => {
  if (rating < 900) return 800;
  if (rating < 1100) return 900;
  if (rating < 1300) return 1100;
  if (rating < 1500) return 1300;
  if (rating < 1700) return 1500;
  return 1700;
};

export default function RatingProgressBar({
  currentRating,
  minRating,
  maxRating,
  categoria,
  showLabel = true,
  size = 'md'
}: RatingProgressBarProps) {
  const min = minRating || getPreviousCategoriaThreshold(currentRating);
  const max = maxRating || getNextCategoriaThreshold(currentRating);
  const progress = ((currentRating - min) / (max - min)) * 100;
  const colors = getCategoriaColor(currentRating);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const textSizes = {
    sm: 'text-[10px] md:text-xs',
    md: 'text-xs md:text-sm',
    lg: 'text-sm md:text-base'
  };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex items-center justify-between mb-1 md:mb-2">
          <div className="flex items-center gap-1 md:gap-2">
            <span className={`${textSizes[size]} font-bold text-textPrimary`}>
              {currentRating}
            </span>
            <span className={`${textSizes[size]} text-textSecondary`}>
              / {max}
            </span>
          </div>
          <span 
            className={`${textSizes[size]} font-bold`}
            style={{ color: colors.from }}
          >
            {categoria || colors.name}
          </span>
        </div>
      )}

      <div className="relative">
        {/* Background bar */}
        <div className={`w-full ${sizeClasses[size]} bg-cardBorder rounded-full overflow-hidden`}>
          {/* Progress bar with gradient */}
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(progress, 100)}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className={`${sizeClasses[size]} rounded-full relative`}
            style={{
              background: `linear-gradient(90deg, ${colors.from}, ${colors.to})`
            }}
          >
            {/* Shine effect */}
            <motion.div
              animate={{
                x: ['-100%', '200%']
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                repeatDelay: 1,
                ease: 'easeInOut'
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
            />
          </motion.div>
        </div>

        {/* Min/Max labels */}
        <div className="flex justify-between mt-1">
          <span className="text-xs text-textSecondary">{min}</span>
          <span className="text-xs text-textSecondary">{max}</span>
        </div>
      </div>

      {/* Points to next category */}
      {currentRating < max && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-textSecondary mt-2 text-center"
        >
          {max - currentRating} puntos para {getCategoriaColor(max).name}
        </motion.p>
      )}
    </div>
  );
}
